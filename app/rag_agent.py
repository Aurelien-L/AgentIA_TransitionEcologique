import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from IPython.display import display, clear_output, Markdown
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain import hub
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from utils.search_chroma import documentSearch, duck_search
from utils.safe_memory import SafeConversationMemory  # ✅ Remplace ConversationBufferMemory

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
            base_prompt = hub.pull("hwchase17/react")
            base_prompt.template = f"{self.system_prompt}\n\n{base_prompt.template}"
            self.prompt = base_prompt
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
        prompt = self.historique_to_prompt(historique)
        print("\n🟦 Prompt envoyé à l’agent :\n", prompt)

        response = self.executor.invoke({"input": prompt})

        print("\n🟩 Résultat brut de l'agent :\n", response)
        return response

    def boucle_interactive(self):
        historique = []
        print("🟢 Assistant transition écologique (entrez 'exit' pour quitter)\n")
        while True:
            user_input = input("Vous : ")
            if user_input.strip().lower() in ["exit", "quit", "stop"]:
                print("👋 Fin de la session.")
                break

            historique.append(HumanMessage(content=user_input))
            clear_output(wait=True)
            display(Markdown(f"**Vous :** {user_input}"))

            response = self.search(historique)

            if "output" in response:
                answer = response["output"].strip()
                if answer == "Agent stopped due to iteration limit or time limit.":
                    answer = (
                        "⏱️ L'agent a été interrompu avant de pouvoir formuler une réponse complète. "
                        "Essayez de reformuler votre question ou augmentez la limite d'itérations."
                    )
                historique.append(AIMessage(content=answer))
                display(Markdown(f"**Assistant :** {answer}"))
            else:
                display(Markdown("**❌ Erreur dans la réponse.**"))
