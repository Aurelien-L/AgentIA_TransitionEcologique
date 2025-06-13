from langchain_ollama import ChatOllama
from langchain import hub
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from utils.search_chroma import documentSearch, duck_search
from utils.safe_memory import SafeConversationMemory

class RagAgent:
    def __init__(self, model, system_prompt: str, use_hub_prompt=True, verbose=True):
        self.model = model
        self.system_prompt = system_prompt

        self.memory = SafeConversationMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output"
        )

        self.tools = [
            Tool(
                name="Recherche documents",
                func=documentSearch,
                description="Utilise les documents internes sur la transition écologique (lois, subventions, etc.)."
            ),
            Tool(
                name="Recherche web",
                func=duck_search,
                description="Utilise une recherche web pour des données à jour sur la transition écologique."
            )
        ]

        if use_hub_prompt:
            self.prompt = hub.pull("hwchase17/react")
        else:
            raise ValueError("Mode 'use_hub_prompt=False' non pris en charge dans cette version")

        self.agent = create_react_agent(
            llm=self.model,
            tools=self.tools,
            prompt=self.prompt
        )

        self.executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=7
        )

    def historique_to_prompt(self, historique):
        prompt = ""
        for message in historique:
            if isinstance(message, HumanMessage):
                prompt += f"Utilisateur : {message.content}\n"
            elif isinstance(message, AIMessage):
                prompt += f"Assistant : {message.content}\n"
        return prompt.strip()

    def search(self, historique):
        messages = [SystemMessage(content=self.system_prompt)] + historique

        injection = (
        "Tu es un agent ReAct. Tu dois OBLIGATOIREMENT suivre ce format exact à chaque étape :\n\n"
        "Question: <question>\n"
        "Thought: <réflexion sur la prochaine étape>\n"
        "Action: <choisir uniquement [Recherche documents] ou [Recherche web]>\n"
        "Action Input: <requête à rechercher>\n"
        "Observation: <résultat obtenu>\n\n"
        "tu termines par :\n"
        "Thought: J'ai réuni suffisamment d'informations.\n"
        "Final Answer: <réponse finale claire et concise en français>\n"
        "Source : <Documents, Web, IA ou combinaison>\n\n"
        "⚠️ Tu DOIS commencer par une [Recherche documents]. C'est OBLIGATOIRE.\n"
        "⚠️ Tu DOIS intégrer les documents trouvés dans ta réponse, même s’ils ne suffisent pas.\n"
        "⚠️ Tu NE PEUX PAS répondre avec l’IA seule, sauf si documents ET web échouent complètement.\n"
        "⚠️ Le web est un dernier recours, jamais le premier.\n"
        "NE DONNE AUCUNE réponse sans source explicite. NE SAUTE AUCUNE ÉTAPE.\n\n"
        "Exemple :\n"
        "Question: Quelle est l’empreinte carbone totale de la France en 2021 ?\n"
        "Thought: Je commence par chercher dans les documents.\n"
        "Action: Recherche documents\n"
        "Action Input: empreinte carbone France 2021\n"
        "Observation: Les documents indiquent environ 663 millions de tonnes équivalent CO2.\n"
        "Thought: J'ai réuni suffisamment d'informations.\n"
        "Final Answer: L'empreinte carbone totale de la France en 2021 était d'environ 663 millions de tonnes équivalent CO2.\n"
        "Source : Documents\n"
        )


        prompt_text = injection + "\n\n" + self.historique_to_prompt(historique)

        print("\n🟦 Prompt envoyé à l’agent :\n", prompt_text)

        # Exécution de l'agent
        response = self.executor.invoke({
            "input": prompt_text,
            "chat_history": messages
        })

        # Extraction du texte brut
        output = response.get("output", "") if isinstance(response, dict) else str(response)

        def filter_output(text: str) -> str:
            lines = text.splitlines()
            final_answer = None
            source = None
            for line in lines:
                lline = line.lower().strip()
                if lline.startswith("final answer:"):
                    final_answer = line.split(":", 1)[1].strip()
                elif lline.startswith("source :"):
                    source = line.split(":", 1)[1].strip()
            if final_answer is None:
                return text.strip()
            if source:
                return f"{final_answer}\n\nSource : {source}"
            return final_answer

        final_output = filter_output(output)

        print("\n🟩 Résultat filtré :\n", final_output)
        return final_output
