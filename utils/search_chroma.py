from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings 
from langchain.schema import Document
from duckduckgo_search import DDGS

# Repertoire où sont stockés les vecteurs 
CHROMA_DIR= "chroma_db"


# Modèle d'embeddings par défaut
EMBEDDING_MODEL = "nomic-embed-text"

def documentSearch(query: str, k: int = 5) -> str : 
    """
    Effectue une recherche vectorielle sur la base ChromaDB pour la requête donnée.
    
    :param query: La requête de l'utilisateur (en langage naturel)
    :param k: Le nombre de documents les plus pertinents à retourner
    :return: Texte formaté des documents trouvés
    """

    # Création embedder (via Ollama ou un autre modèle) 
    embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)

    # Chargement base vectorielle
    vectordb = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embedding
    )

    # lancement recherc h de k documents les plus pertinents 
    results = vectordb.similarity_search(query, k=k)

    # Formattage résultats pour un retour clair 
    if not results:
        return "Aucun document trouvé"
    
    formatted = []

    for i, doc in enumerate(results, 1):
        formatted.append(
            f"🔹 Résultat {i}:\n{doc.page_content[:500]}...\n(Source: {doc.metadata.get('source_file', 'inconnu')})\n"
        )
    
    return "\n".join(formatted)

def duck_search(message: str) -> str:
    with DDGS() as ddgs:
        results = ddgs.text(message, max_results=7)
        snippets = "\n".join([r["body"] for r in results if "body" in r])
    return snippets or "Aucune information trouvée sur le web."