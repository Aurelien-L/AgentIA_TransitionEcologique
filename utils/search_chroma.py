from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.vectorstores import Chroma as VectorstoreChroma
from langchain.schema import Document
from duckduckgo_search import DDGS
import time

CHROMA_DIR = "chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"

# Initialisation globale pour réutilisation
embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)
vectordb = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embedding
)
retriever = vectordb.as_retriever(search_kwargs={"k": 24})

def documentSearch(query: str, k: int = 8) -> str:
    """
    Lance une recherche vectorielle via retriever
    """
    docs = retriever.get_relevant_documents(query)

    if not docs:
        return "Aucun document trouvé"

    results = []
    for i, doc in enumerate(docs, 1):
        results.append(
            f"🔹 Résultat {i}:\n{doc.page_content[:500]}...\n(Source: {doc.metadata.get('source_file', 'inconnu')})\n"
        )
    return "\n".join(results)

_cache_duck_search = {}

def duck_search(query: str, max_retries=3, retry_delay=5) -> str:
    # Cache en mémoire
    if query in _cache_duck_search:
        return _cache_duck_search[query]

    attempt = 0
    while attempt < max_retries:
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=7)
                snippets = "\n".join([r["body"] for r in results if "body" in r])
                response = snippets or "Aucune information trouvée sur le web."
                
                # Stockage en cache
                _cache_duck_search[query] = response
                
                print(f"[duck_search] Requête réussie pour : {query}")
                return response

        except Exception as e:
            print(f"[duck_search] Erreur lors de la recherche web : {e}")
            attempt += 1
            if attempt < max_retries:
                print(f"[duck_search] Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
            else:
                print(f"[duck_search] Échec après {max_retries} tentatives.")
                return "Erreur lors de la recherche web, veuillez réessayer plus tard."
