import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .rag_agent import RagAgent

USE_DEEPSEEK = True  # ⬅️ Mets sur False pour revenir à Llama3

# Ceci permet d'utiliser des modèles en ligne comme gpt-x, deepseek-x, etc...
load_dotenv(override=True) 
# 🔁 Choix du modèle

if load_dotenv(override=True) and USE_DEEPSEEK:
    MODEL_NAME = "deepseek-chat"
    llm = ChatDeepSeek(model=MODEL_NAME, api_key=os.getenv("DEEPSEEK_API_KEY"))
else:
    MODEL_NAME = "llama3"
    llm = ChatOllama(model=MODEL_NAME, temperature=0)

SYSTEM_PROMPT = """
Vous êtes un assistant intelligent utilisant la méthode ReAct (Reasoning + Acting).

Pour répondre à la question de l'utilisateur, vous devez suivre ce format précis et strict, étape par étape :

Question: <question posée par l'utilisateur>

Thought: <votre réflexion sur la prochaine étape à effectuer>

Action: <choisissez exactement une action parmi : "Recherche documents" ou "Recherche web">

Action Input: <la requête exacte que vous envoyez à cette action>

Observation: <les résultats ou informations obtenues suite à l'action>

Vous pouvez répéter autant de fois que nécessaire la séquence Thought → Action → Action Input → Observation.

Quand vous disposez d'assez d'informations pour répondre, terminez par :

Thought: J'ai réuni suffisamment d'informations.

Final Answer: <votre réponse complète et concise en français>

Important :  
- Après chaque Thought, vous devez obligatoirement spécifier une Action.  
- L'Action doit être exactement "Recherche documents" ou "Recherche web".  
- Respectez strictement la casse, la ponctuation, les espaces et le format indiqué.  
- Ne donnez aucune explication ou commentaire hors du cadre indiqué.  
- La réponse finale doit être factuelle, claire et concise.
- Termine toujours la réponse finale par : **Source : <...>** (Documents, Web, IA ou une combinaison).
"""

RESPONSE_MARKERS = [
    "réponse :", 
    "final answer", 
    "voici ce que je recommande", 
    "donc", 
    "en résumé",
    "source :"
]

class ChatModel:
    def __init__(self, model=llm, system_prompt=SYSTEM_PROMPT):
        self.system_prompt = system_prompt
        self.llm = model
        self.historique = [SystemMessage(content=system_prompt)]
        self.agent_rag = RagAgent(self.llm, system_prompt=self.system_prompt)

    def model_response(self, message: str) -> str:
        self.historique.append(HumanMessage(content=message))

        try:
            rag_response = self.agent_rag.search(self.historique)
            if isinstance(rag_response, dict):
                output = rag_response.get("output", "").strip()
            else:
                output = str(rag_response).strip()
        except Exception as e:
            print(f"[⚠️ Erreur RagAgent] {e}")
            output = ""

        is_short = len(output) < 20
        is_generic = output.lower() in ["je ne sais pas.", "je ne suis pas sûr.", ""]
        lacks_final = not any(marker in output.lower() for marker in RESPONSE_MARKERS)
        missing_source_tag = not "source :" in output.lower()

        if is_short or is_generic or lacks_final or missing_source_tag:
            try:
                response = self.llm.invoke(self.historique)
                output = response.content.strip()
            except Exception as e:
                print(f"[⚠️ Erreur modèle principal] {e}")
                output = "Je ne sais pas."

        self.historique.append(AIMessage(content=output))
        return output
