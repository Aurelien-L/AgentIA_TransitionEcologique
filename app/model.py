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
Tu es un assistant intelligent spécialisé dans les questions liées à la transition écologique.

Tu suis la méthode ReAct (Reasoning + Acting) avec les règles suivantes :

1. Tu DOIS toujours commencer par une **Recherche documents**.
2. Tu dois OBLIGATOIREMENT inclure les résultats de la recherche documentaire dans ta réponse finale, même partiellement.
3. Tu ne peux effectuer une **Recherche web** que si les documents ne suffisent pas, et tu dois le justifier dans ta réflexion.
4. Tu ne peux faire de **raisonnement IA** (sans source) qu’en tout dernier recours absolu, et uniquement si les documents ET le web sont vides ou non pertinents.
5. Ta réponse finale doit être fondée sur des sources et contenir obligatoirement la mention :  
   **Source : Documents, Web, IA ou combinaison**

**Format strict à respecter à chaque étape :**

Question: <question de l'utilisateur>  
Thought: <ta réflexion sur la prochaine étape>  
Action: <choisis uniquement "Recherche documents" ou "Recherche web">  
Action Input: <requête à rechercher>  
Observation: <résultat de la recherche>  

tu termines par :  
Thought: J'ai réuni suffisamment d'informations.  
Final Answer: <réponse finale claire et concise, en français>  
Source : <indique la ou les sources utilisées : Documents, Web, IA ou combinaison>

---

Exemple :

Question: Quelle est l’empreinte carbone totale de la France en 2021 ?  
Thought: Je commence par chercher dans les documents officiels.  
Action: Recherche documents  
Action Input: empreinte carbone France 2021  
Observation: Les documents indiquent que l’empreinte carbone totale était d’environ 663 millions de tonnes équivalent CO2.  
Thought: J'ai réuni suffisamment d'informations.  
Final Answer: L'empreinte carbone totale de la France en 2021 était d'environ 663 millions de tonnes équivalent CO2.  
Source : Documents

---

⚠️ NE JAMAIS donner de réponse IA sans avoir exploité les documents.  
⚠️ Le Web est un complément optionnel si les documents sont insuffisants.  
⚠️ Ne saute aucune étape, ne change jamais le format, respecte strictement la structure.
"""


RESPONSE_MARKERS = ["réponse", "final answer", "source :"]

class ChatModel:
    def __init__(self, model=llm, system_prompt=SYSTEM_PROMPT):
        self.system_prompt = system_prompt
        self.llm = model
        self.historique = [SystemMessage(content=system_prompt)]
        self.agent_rag = RagAgent(self.llm, system_prompt=system_prompt)

    def _filter_final_answer_and_source(self, text: str) -> str:
        final_answer = None
        source = None

        for line in text.splitlines():
            line_lower = line.lower().strip()
            if line_lower.startswith("final answer:"):
                final_answer = line.split(":", 1)[1].strip()
            elif line_lower.startswith("source :"):
                source = line.split(":", 1)[1].strip()

        if final_answer is None:
            return text.strip()

        if source:
            return f"{final_answer}\n\nSource : {source}"
        else:
            return final_answer

    def model_response(self, message: str) -> str:
        self.historique.append(HumanMessage(content=message))

        try:
            rag_response = self.agent_rag.search(self.historique)

            # ✅ Nouvelle version tolérante : dict ou str
            if isinstance(rag_response, dict) and "output" in rag_response:
                output = rag_response["output"].strip()
            elif isinstance(rag_response, str):
                output = rag_response.strip()
            else:
                output = ""

        except Exception as e:
            print(f"[⚠️ Erreur RagAgent] {e}")
            output = ""

        if len(output) < 20 or not any(m in output.lower() for m in RESPONSE_MARKERS):
            try:
                output = self.llm.invoke(self.historique).content.strip()
            except Exception as e:
                print(f"[⚠️ Erreur LLM direct] {e}")
                output = "Je ne sais pas."

        filtered_output = self._filter_final_answer_and_source(output)

        self.historique.append(AIMessage(content=filtered_output))
        return filtered_output

