from langchain_ollama import ChatOllama
from langchain import hub
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from utils.search_chroma import documentSearch, duck_search
from utils.safe_memory import SafeConversationMemory

class RagAgent:
    """
    Classe RagAgent qui encapsule un agent ReAct (Reasoning + Acting) combinant
    recherche documentaire et recherche web pour répondre aux questions.

    Cet agent utilise LangChain avec des outils (tools) configurés pour faire
    des recherches dans des documents internes et sur le web (via DuckDuckGo),
    en suivant un prompt strict imposant une méthode étape par étape.

    Attributs :
        model : Le modèle LLM utilisé (ex: ChatOllama, ChatDeepSeek).
        system_prompt (str) : Le prompt système général donné au modèle.
        memory : Mémoire conversationnelle sécurisée pour stocker l'historique.
        tools (list) : Liste des outils (documentSearch et duck_search) pour les actions.
        prompt : Prompt spécifique tiré du hub LangChain (ex: "hwchase17/react").
        agent : Agent ReAct créé avec les outils et le modèle.
        executor : Exécuteur pour gérer les interactions entre agent, mémoire et outils.
    """

    def __init__(self, model, system_prompt: str, use_hub_prompt=True, verbose=True):
        """
        Initialise l'agent RagAgent avec le modèle, le prompt système et la configuration.

        Args:
            model : Modèle LLM à utiliser pour l'agent.
            system_prompt (str) : Prompt système pour cadrer la conversation.
            use_hub_prompt (bool) : Si True, récupère le prompt depuis LangChain Hub.
            verbose (bool) : Active les logs détaillés.
        
        Raises:
            ValueError : Si use_hub_prompt est False (non supporté ici).
        """
        self.model = model
        self.system_prompt = system_prompt

        # Initialise une mémoire de conversation sécurisée avec clés pour l'entrée/sortie
        self.memory = SafeConversationMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="output"
        )

        # Définition des outils à disposition de l'agent
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

        # Chargement du prompt ReAct depuis le hub LangChain si demandé
        if use_hub_prompt:
            self.prompt = hub.pull("hwchase17/react")
        else:
            raise ValueError("Mode 'use_hub_prompt=False' non pris en charge dans cette version")

        # Création de l'agent ReAct avec le modèle, les outils et le prompt
        self.agent = create_react_agent(
            llm=self.model,
            tools=self.tools,
            prompt=self.prompt
        )

        # Création de l'exécuteur d'agent, avec mémoire et gestion d'erreurs
        self.executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=7  # Limite du nombre d'itérations de réflexion/actes
        )

    def historique_to_prompt(self, historique):
        """
        Convertit l'historique des messages en une chaîne de texte formatée.

        Args:
            historique (list): Liste des messages HumanMessage et AIMessage.

        Returns:
            str: Texte concaténé avec préfixes "Utilisateur :" et "Assistant :"
        """
        prompt = ""
        for message in historique:
            if isinstance(message, HumanMessage):
                prompt += f"Utilisateur : {message.content}\n"
            elif isinstance(message, AIMessage):
                prompt += f"Assistant : {message.content}\n"
        return prompt.strip()

    def search(self, historique):
        """
        Lance une recherche et interaction avec l'agent ReAct à partir de l'historique.

        Cette méthode construit un prompt complet incluant un "injection" avec les règles
        strictes à suivre, puis exécute l'agent avec l'historique donné, et filtre la sortie
        pour extraire la réponse finale et les sources.

        Args:
            historique (list): Liste des messages précédents (HumanMessage, AIMessage).

        Returns:
            str: Réponse finale filtrée contenant la réponse et la source.
        """
        # Combine le prompt système et l'historique en messages
        messages = [SystemMessage(content=self.system_prompt)] + historique

        # Injection du prompt ReAct strict détaillant les règles à suivre
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

        # Construction finale du prompt envoyé à l'agent
        prompt_text = injection + "\n\n" + self.historique_to_prompt(historique)

        print("\n🟦 Prompt envoyé à l’agent :\n", prompt_text)

         # Invocation de l'agent avec le prompt et l'historique de conversation
        response = self.executor.invoke({
            "input": prompt_text,
            "chat_history": messages
        })

        # Extraction du texte de sortie brut
        output = response.get("output", "") if isinstance(response, dict) else str(response)

        def filter_output(text: str) -> str:
            """
            Filtre la sortie brute pour extraire la réponse finale et la source.

            Args:
                text (str): Texte brut généré par l'agent.

            Returns:
                str: Réponse finale formatée avec la source si présente.
            """
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
        
        # Application du filtre sur la sortie brute
        final_output = filter_output(output)

        print("\n🟩 Résultat filtré :\n", final_output)
        return final_output
