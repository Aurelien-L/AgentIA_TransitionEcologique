import sys
import os

# Ajouter le dossier racine à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from IPython.display import display, clear_output, Markdown
from dotenv import load_dotenv
from datetime import datetime
from langchain_ollama import ChatOllama
#from langchain_deepseek import ChatDeepSeek
from langchain import hub
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
import re
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
#from LLM.utils.rag.document import document_search
#from LLM.utils.rag.web_search import web_search

from utils.search_chroma import *
from duck_search import duck_search


SPECIALIZED_INSTRUCTION = """
Tu es un assistant intelligent expert en **transition écologique**. Ton objectif est d’aider les citoyens à comprendre :
- les lois et réglementations,
- les subventions ou aides disponibles,
- les bonnes pratiques pour la transition énergétique et environnementale.
- Tu t’exprimes **en français clair**, sans emoji, ni fioritures.

Tu as accès à deux outils :
1. **Recherche documents** : pour chercher dans les documents internes fiables (ex. législation, politiques publiques, aides existantes).
2. **Recherche web** : pour compléter avec des données à jour disponibles sur Internet si les documents internes ne suffisent pas.

---

Lorsque tu réponds :
- Utilise **d'abord** l’outil `Recherche documents`.
- Si l’information n’est **pas disponible ou insuffisante**, utilise `Recherche web`.
- Tu **dois toujours suivre la structure ReAct** :

Exemple de raisonnement attendu :
Thought: Je dois chercher la réglementation actuelle sur les panneaux solaires.
Action: Recherche documents
Action Input: réglementation panneaux solaires France 2024


Puis, après avoir reçu l'information :

Observation: Voici les résultats des documents internes...
Pensée: Les documents internes répondent bien à la question.
Réponse: En 2024, les règles pour les panneaux solaires sont...


---

Tu ne dois **jamais inventer une réponse**.
Si aucune information fiable n’est disponible après les recherches, réponds simplement : `Je ne sais pas.`

Tu t’exprimes **en français clair**, sans emoji, ni fioritures.

---

Voici la question :

"""

class RagAgent:
    def __init__(self, model, use_hub_prompt=True):
        self.model = model

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
            ),
        ]

        if use_hub_prompt:
            base_prompt = hub.pull("hwchase17/react")  # ReAct de base
            # Fusionne instruction spécialisée et prompt de base
            base_prompt.template = f"{SPECIALIZED_INSTRUCTION}\n\n{base_prompt.template}"
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
            verbose=True,
            handle_parsing_errors=True
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
        return self.executor.invoke({"input": prompt})

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
                answer = response["output"]
                historique.append(AIMessage(content=answer))
                display(Markdown(f"**Assistant :** {answer}"))
            else:
                display(Markdown("**Erreur dans la réponse.**"))

    
if __name__ == "__main__":
    agent = RagAgent(ChatOllama(model="llama3"))
    agent.boucle_interactive()

