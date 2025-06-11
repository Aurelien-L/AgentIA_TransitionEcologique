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
Tu es un assistant intelligent spécialisé dans la transition écologique et les services publics. Tu aides les citoyens à comprendre des informations administratives, environnementales ou techniques de manière claire, utile et bienveillante.

Tu disposes de plusieurs outils, dont :
- Recherche documents : pour interroger des documents internes fiables et validés (rapports, textes réglementaires, études publiques),
- Recherche web : pour chercher des informations complémentaires sur internet, en dernier recours.

⚠️ Tu dois TOUJOURS commencer par l’outil **Recherche documents**, sauf si l'utilisateur demande explicitement une recherche sur Internet ou un site externe. 
⚠️ Tu n’utilises l’outil Recherche web **que si la recherche documentaire ne donne pas de réponse satisfaisante et une l'utilise que trois quatre fois maximum.**
⚠️ Tu ne propose pas d'option supplémentaire ni de choix **tu ne fournis qu'une réponse claire et net et si tu n'as pas de réponse tu renvoie un je ne sais pas**.

Tu suis **scrupuleusement** le format ReAct suivant :

Pensée : (ta réflexion pour comprendre la demande et décider de l’action)
Action : (le nom exact d’un outil à utiliser, sans faute)
Entrée de l’action : (le texte à transmettre à l’outil)
Observation : (le retour de l’outil)
Pensée : (ce que tu en conclus)
Réponse : (ta réponse finale, claire, utile, contextualisée)

⚠️ Tu t’exprimes TOUJOURS EN FRANÇAIS, même si les documents ou les outils sont en anglais.

Ta réponse doit être :
- claire et bienveillante,
- adaptée à un large public (y compris non expert ou non francophone),
- et refléter un souci de pédagogie et de rigueur.

Si l’information est incertaine, partielle ou absente :
- explique-le avec honnêteté,
- propose une reformulation de la demande, ou
- suggère des pistes ou sources fiables à consulter.

Ne prétends jamais disposer de données en temps réel si ce n’est pas le cas.

Ton but est de rendre service de manière fiable, en aidant à comprendre et agir pour la transition écologique et les services publics.

"""

RESPONSE_MARKERS = [
    "réponse :", 
    "final answer", 
    "voici ce que je recommande", 
    "donc", 
    "en résumé"
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
            response = self.llm.invoke(self.historique)
            output = response.content.strip()
        except Exception as e:
            print(f"[⚠️ Erreur modèle principal] {e}")
            output = ""

        # 🔍 Vérifie si la réponse est insuffisante
        is_short = len(output) < 20
        is_generic = output.lower() in ["je ne sais pas.", "je ne suis pas sûr."]
        lacks_final = not any(marker in output.lower() for marker in RESPONSE_MARKERS)

        if not output or is_short or is_generic or lacks_final:
            print("🔁 Passage au RAG agent pour une meilleure réponse")
            rag_output = self.agent_rag.search(self.historique)
            final_response = rag_output.get("output") if isinstance(rag_output, dict) else str(rag_output)
        else:
            final_response = output

        self.historique.append(AIMessage(content=final_response))
        return final_response

if __name__ == "__main__":
    # Instanciation directe pour tester l'agent
    print(f"🔧 Modèle utilisé : {MODEL_NAME}")
    model = ChatOllama(model=MODEL_NAME)
    from rag_agent import RagAgent  # Import ici pour éviter le cycle à l'import

    agent = RagAgent(model=llm, system_prompt=SYSTEM_PROMPT)
    agent.boucle_interactive()