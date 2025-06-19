import hashlib
import time
import logging

from duckduckgo_search import DDGS
from langchain.memory import ConversationBufferMemory
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

"""
Ce module fournit deux fonctions principales :
1. `documentSearch(query)` pour effectuer une recherche vectorielle dans une base Chroma locale.
2. `duck_search(query)` pour lancer une recherche web à l’aide de DuckDuckGo.

Il utilise des embeddings générés par Ollama (`nomic-embed-text`) et supporte un cache pour les recherches web.
"""

# Paramètres globaux
CHROMA_DIR = "chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"

# Création des embeddings avec Ollama
embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)

def create_advanced_retriever(k=20, threshold=0.8):
    """
    Crée un retriever MMR avec suppression de doublons et filtrage par score.

    Args:
        k (int): Nombre de documents retournés.
        threshold (float): Seuil minimal de similarité (entre 0 et 1).

    Returns:
        callable: fonction de recherche vectorielle avancée prenant une requête string.
    """
    vectordb = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embedding
    )

    retriever = vectordb.as_retriever(
        search_type="mmr",  # max marginal relevance = diversité + pertinence
        search_kwargs={
            "k": k,
            "fetch_k": 50,
            "lambda_mult": 0.5
        }
    )

    def deduplicate(docs):
        """Élimine les doublons exacts en hachant le contenu."""
        seen = set()
        uniques = []
        for doc in docs:
            h = hashlib.md5(doc.page_content.encode()).hexdigest()
            if h not in seen:
                uniques.append(doc)
                seen.add(h)
        return uniques

    def search(query):
        """Recherche dans la base vectorielle avec filtres."""
        docs = retriever.get_relevant_documents(query)
        filtered_docs = [d for d in docs if d.metadata.get("score", 1.0) >= threshold]
        return deduplicate(filtered_docs)

    return search

# Initialise le retriever avancé
advanced_search = create_advanced_retriever(k=24, threshold=0.78)

def documentSearch(query: str, k: int = 24) -> str:
    """
    Lance une recherche vectorielle avancée sur les documents indexés.

    Args:
        query (str): Question utilisateur.
        k (int): Nombre de documents max à retourner.

    Returns:
        str: Résumé formaté des résultats trouvés.
    """
    docs = advanced_search(query)

    if not docs:
        return "Aucun document trouvé."

    results = []
    for i, doc in enumerate(docs, 1):
        results.append(
            f"🔹 Résultat {i}:\n{doc.page_content[:500]}...\n(Source: {doc.metadata.get('source_file', 'inconnu')})\n"
        )
    return "\n".join(results)


def duck_search(query: str, max_results: int = 5, retries: int = 3, delay: float = 1.5) -> str:
    """
    Lance une recherche web robuste via DuckDuckGo avec relances.

    Args:
        query (str): Sujet à rechercher.
        max_results (int): Nombre max de résultats à retourner.
        retries (int): Nombre de tentatives.
        delay (float): Pause (en secondes) entre chaque tentative.

    Returns:
        str: Résultats formatés ou message d’échec.
    """
    for attempt in range(1, retries + 1):
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, region="fr-fr", safesearch="Moderate", max_results=max_results):
                    title = r.get("title", "Sans titre")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    results.append(f"🔗 {title}\n{body}\n➡️ {href}\n")

            if results:
                return "\n".join(results)

        except Exception as e:
            print(f"[Tentative {attempt}] Erreur DuckDuckGo : {e}")

        time.sleep(delay)  # Petite pause avant nouvelle tentative

    return "Aucun résultat web trouvé après plusieurs tentatives."
