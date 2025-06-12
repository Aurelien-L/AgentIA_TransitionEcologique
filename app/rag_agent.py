import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
            "Tu es un agent ReAct utilisant STRICTEMENT le format suivant à chaque étape :\n"
            "\n"
            "Question: <question>\n"
            "Thought: <réflexion>\n"
            "Action: <choisir exactement 'Recherche documents' ou 'Recherche web'>\n"
            "Action Input: <requête pour l'action choisie>\n"
            "Observation: <résultat obtenu>\n"
            "\n"
            "Tu répètes cette séquence autant de fois que nécessaire.\n"
            "Quand tu as assez d'infos, termine par :\n"
            "Thought: J'ai réuni suffisamment d'informations.\n"
            "Final Answer: <réponse concise et claire en français>\n"
            "Source : <Documents, Web, IA ou combinaison>\n"
            "\n"
            "Respecte STRICTEMENT ce format, ne saute aucune étape, ne donne aucune info hors cadre.\n"
            "Priorise toujours dans l'ordre : Recherche documents → Recherche web → Raisonnement IA.\n"
        )

        prompt_text = injection + "\n\n" + self.historique_to_prompt(historique)

        print("\n🟦 Prompt envoyé à l’agent :\n", prompt_text)

        response = self.executor.invoke({
            "input": prompt_text,
            "chat_history": messages
        })

        print("\n🟩 Résultat brut de l'agent :\n", response)
        return response