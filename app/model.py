import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .rag_agent import RagAgent

USE_DEEPSEEK = True  # ⬅️ Mets sur False pour revenir à Llama3

# Chargement des variables d'environnement depuis un fichier .env
load_dotenv(override=True) 

# 🔁 Choix du modèle à utiliser selon la variable USE_DEEPSEEK et la présence des clés d'API
if load_dotenv(override=True) and USE_DEEPSEEK:
    MODEL_NAME = "deepseek-chat"  # Nom du modèle DeepSeek à utiliser
    # Initialisation de l'instance LLM DeepSeek avec clé API récupérée dans les variables d'environnement
    llm = ChatDeepSeek(model=MODEL_NAME, api_key=os.getenv("DEEPSEEK_API_KEY"))
else:
    MODEL_NAME = "llama3"  # Sinon on revient à Llama3
    # Initialisation du modèle Llama3 avec température 0 (réponses déterministes)
    llm = ChatOllama(model=MODEL_NAME, temperature=0)

# PROMPT SYSTÈME utilisé pour guider le comportement de l'assistant intelligent
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


# Liste des mots clés pour détecter une réponse finale dans la sortie du modèle
RESPONSE_MARKERS = ["réponse", "final answer", "source :"]

class ChatModel:
    """
    Classe représentant le modèle de chat intelligent combinant un LLM (DeepSeek ou Llama3)
    avec un agent RAG (Recherche Augmentée par Génération) pour gérer la logique ReAct.
    """

    def __init__(self, model=llm, system_prompt=SYSTEM_PROMPT):
        """
        Initialise le modèle de chat avec un modèle LLM et un prompt système.

        Args:
            model: instance du modèle LLM (par défaut celui choisi plus haut)
            system_prompt: chaîne de caractères définissant le prompt système pour guider l'agent
        """
        self.system_prompt = system_prompt
        self.llm = model
        # Historique des messages échangés (avec un message système initial)
        self.historique = [SystemMessage(content=system_prompt)]
        # Initialisation de l'agent RAG avec le même LLM et prompt
        self.agent_rag = RagAgent(self.llm, system_prompt=system_prompt)

    def _filter_final_answer_and_source(self, text: str) -> str:
        """
        Extrait la réponse finale et la source dans le texte renvoyé par l'agent,
        en respectant le format attendu (final answer + source).

        Args:
            text: chaîne de caractères contenant la sortie brute du modèle

        Returns:
            Une chaîne avec uniquement la réponse finale et la source formatée,
            ou le texte original si aucun marqueur n'a été trouvé.
        """
        final_answer = None
        source = None

        # Analyse ligne par ligne pour trouver "final answer" et "source"
        for line in text.splitlines():
            line_lower = line.lower().strip()
            if line_lower.startswith("final answer:"):
                final_answer = line.split(":", 1)[1].strip()
            elif line_lower.startswith("source :"):
                source = line.split(":", 1)[1].strip()

        # Si aucune réponse finale, on retourne le texte brut (ex : message d'erreur)
        if final_answer is None:
            return text.strip()

        # Si la source est présente, on la concatène proprement à la réponse finale
        if source:
            return f"{final_answer}\n\nSource : {source}"
        else:
            return final_answer

    def model_response(self, message: str) -> str:
        """
        Traite un message utilisateur, interroge l'agent RAG, gère les exceptions,
        filtre la réponse pour ne garder que la réponse finale et la source,
        et met à jour l'historique de la conversation.

        Args:
            message: message texte de l'utilisateur

        Returns:
            La réponse finale formatée à retourner à l'utilisateur.
        """
        # Ajout du message utilisateur à l'historique
        self.historique.append(HumanMessage(content=message))

        try:
            # Recherche via l'agent RAG avec l'historique complet
            rag_response = self.agent_rag.search(self.historique)

            # Gestion tolérante selon que la réponse est dict ou str
            if isinstance(rag_response, dict) and "output" in rag_response:
                output = rag_response["output"].strip()
            elif isinstance(rag_response, str):
                output = rag_response.strip()
            else:
                output = ""

        except Exception as e:
            # En cas d'erreur dans RagAgent, on affiche un avertissement et continue
            print(f"[⚠️ Erreur RagAgent] {e}")
            output = ""

        # Si la sortie est trop courte ou ne contient pas les mots clés attendus,
        # on appelle directement le LLM en fallback
        if len(output) < 20 or not any(m in output.lower() for m in RESPONSE_MARKERS):
            try:
                output = self.llm.invoke(self.historique).content.strip()
            except Exception as e:
                # En cas d'erreur LLM direct, on retourne une réponse générique
                print(f"[⚠️ Erreur LLM direct] {e}")
                output = "Je ne sais pas."

        # On filtre la sortie pour garder uniquement la réponse finale et la source
        filtered_output = self._filter_final_answer_and_source(output)

        # On ajoute la réponse AI à l'historique pour conserver le contexte
        self.historique.append(AIMessage(content=filtered_output))

        # Retour de la réponse finale filtrée
        return filtered_output

