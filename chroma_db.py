import hashlib
import time
import json
from pathlib import Path
import pandas as pd

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from utils.chroma.run_cleaning import clean_all

DEFAULT_CLEAN_DIR = Path("data/clean")
DEFAULT_CHROMA_DIR = Path("chroma_db")
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"

CACHE_FILE = Path("index_cache.json")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
MAX_CHUNKS = 1000
BATCH_SIZE_INDEX = 500


def log_time(label: str, start: float):
    """
    Affiche le temps écoulé depuis un point de départ.

    Args:
        label (str): Nom de l'étape mesurée.
        start (float): Timestamp de départ.
    """
    print(f"⏱️ {label}: {time.time() - start:.2f}s")


def generate_chunk_id(text: str) -> str:
    """
    Génère un identifiant unique (hash MD5) à partir d'un texte.

    Args:
        text (str): Texte à hasher.

    Returns:
        str: Hash MD5 du texte.
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def hash_file(path: Path) -> str:
    """
    Calcule un hash MD5 pour le contenu binaire d'un fichier.

    Args:
        path (Path): Chemin du fichier.

    Returns:
        str: Hash MD5 du fichier.
    """
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def load_cache() -> dict:
    """
    Charge le cache de hachage depuis un fichier JSON.

    Returns:
        dict: Cache contenant les hachages précédents des fichiers.
    """
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """
    Sauvegarde le cache de hachage dans un fichier JSON.

    Args:
        cache (dict): Dictionnaire de hachages à sauvegarder.
    """
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def load_parquet_documents(clean_dir: Path, changed_files: set[str]) -> list[Document]:
    """
    Charge les fichiers .parquet modifiés et crée des documents LangChain.

    Args:
        clean_dir (Path): Répertoire contenant les fichiers nettoyés.
        changed_files (set[str]): Fichiers à recharger (modifiés).

    Returns:
        list[Document]: Documents extraits à partir des fichiers .parquet.
    """
    documents = []
    for file in clean_dir.rglob("*.parquet"):
        if file.name not in changed_files:
            # On ignore les fichiers non modifiés
            continue
        df = pd.read_parquet(file)
        for _, row in df.iterrows():
            text = " | ".join(str(value) for value in row.values if pd.notna(value)).strip()
            if text:
                documents.append(Document(
                    page_content=text,
                    metadata={"source_file": file.name}
                ))
    return documents


def get_existing_ids(chroma_dir: Path) -> set[str]:
    """
    Récupère les IDs de documents déjà indexés dans la base Chroma.

    Args:
        chroma_dir (Path): Répertoire de persistance de la base Chroma.

    Returns:
        set[str]: Ensemble des identifiants indexés.
    """
    if not chroma_dir.exists():
        return set()
    try:
        db = Chroma(persist_directory=str(chroma_dir), embedding_function=None)
        return set(db.get()['ids'])
    except Exception as e:
        print(f"⚠️ Impossible de récupérer les IDs existants : {e}")
        return set()


def index_documents(
    clean_dir: Path = DEFAULT_CLEAN_DIR,
    chroma_dir: Path = DEFAULT_CHROMA_DIR,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    embedding=None,
    max_retries: int = 3,          # nombre max de tentatives par batch
    retry_delay: float = 2.0,      # délai entre retries en secondes
    batch_delay: float = 1.0       # délai entre batches en secondes
) -> dict | None:
    global_start = time.time()

    print("🔍 Chargement du cache de hash fichiers...")
    cache = load_cache()

    print("📥 Recherche des fichiers .parquet modifiés ou nouveaux...")
    changed_files = set()
    for file in clean_dir.rglob("*.parquet"):
        current_hash = hash_file(file)
        cached_hash = cache.get(file.name)
        if current_hash != cached_hash:
            print(f"🆕 Fichier modifié ou nouveau détecté: {file.name}")
            changed_files.add(file.name)
            cache[file.name] = current_hash

    if not changed_files:
        print("✅ Aucun fichier modifié. Pas besoin de réindexer.")
        return None

    print(f"📥 Chargement des documents des fichiers modifiés ({len(changed_files)})...")
    start = time.time()
    raw_docs = load_parquet_documents(clean_dir, changed_files)
    log_time("Chargement", start)
    print(f"✅ {len(raw_docs)} documents bruts chargés.")

    if not raw_docs:
        print("⚠️ Aucun document à traiter après filtre. Fin de la pipeline.")
        return None

    print("🧹 Déduplication des documents...")
    start = time.time()
    seen = set()
    unique_docs = []
    for doc in raw_docs:
        h = generate_chunk_id(doc.page_content)
        if h not in seen:
            seen.add(h)
            unique_docs.append(doc)
    log_time("Déduplication", start)
    print(f"✅ {len(unique_docs)} documents uniques après déduplication.")

    print("🔪 Découpage des documents en chunks...")
    start = time.time()
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = []
    for doc in unique_docs:
        content = doc.page_content.strip()
        if len(content) < CHUNK_SIZE:
            if len(content) > 50:
                chunks.append(doc)
        else:
            chunks.extend(splitter.split_documents([doc]))
    log_time("Découpage", start)
    print(f"✅ {len(chunks)} chunks générés.")

    print("🆔 Attribution des IDs aux chunks...")
    for chunk in chunks:
        chunk.metadata["id"] = generate_chunk_id(chunk.page_content)

    print("📂 Récupération des IDs déjà indexés dans Chroma...")
    existing_ids = get_existing_ids(chroma_dir)

    new_chunks = [chunk for chunk in chunks if chunk.metadata["id"] not in existing_ids]
    print(f"🆕 {len(new_chunks)} nouveaux chunks à indexer.")

    if not new_chunks:
        print("✅ Aucun nouveau chunk à indexer. Fin de la pipeline.")
        return {
            "raw_docs": len(raw_docs),
            "unique_docs": len(unique_docs),
            "chunks": len(chunks),
            "indexed": 0,
        }

    new_chunks = new_chunks[:MAX_CHUNKS]

    print("🧠 Indexation dans Chroma (par batch)...")
    start = time.time()
    embedding = embedding or OllamaEmbeddings(model=embedding_model)
    vectordb = Chroma(persist_directory=str(chroma_dir), embedding_function=embedding)

    total = len(new_chunks)
    batches = [new_chunks[i:i + BATCH_SIZE_INDEX] for i in range(0, total, BATCH_SIZE_INDEX)]

    successful_index = False

    for i, batch in enumerate(batches, 1):
        batch_ids = [chunk.metadata["id"] for chunk in batch]
        attempt = 0
        while attempt < max_retries:
            try:
                vectordb.add_documents(batch, ids=batch_ids)
                print(f"✅ Batch {i}/{len(batches)} indexé (tentative {attempt + 1}).")
                successful_index = True
                break
            except Exception as e:
                attempt += 1
                print(f"❌ Erreur lors de l’indexation batch {i} (tentative {attempt}): {e}")
                if attempt < max_retries:
                    print(f"🔄 Nouvelle tentative dans {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"⚠️ Échec définitif du batch {i} après {max_retries} tentatives.")
        time.sleep(batch_delay)

    log_time("Pipeline complète", global_start)

    if successful_index:
        save_cache(cache)
        print("✅ Mise à jour de Chroma et cache terminée avec succès.")
    else:
        print("⚠️ Aucun batch n’a été indexé avec succès. Le cache n’a pas été mis à jour.")

    return {
        "raw_docs": len(raw_docs),
        "unique_docs": len(unique_docs),
        "chunks": len(chunks),
        "indexed": len(new_chunks) if successful_index else 0,
    }
    
        
def update_file_in_index(
    file_path: Path,
    chroma_dir: Path = DEFAULT_CHROMA_DIR,
    embedding_model: str = "nomic-embed-text",
):
    """
    Met à jour la base Chroma pour un seul fichier .parquet donné.

    Args:
        file_path (Path): Chemin vers le fichier à indexer.
        chroma_dir (Path): Répertoire de la base Chroma.
        embedding_model (str): Nom du modèle d'embedding.
    """
    # Charger le fichier (exemple CSV/Parquet)
    import pandas as pd
    df = pd.read_parquet(file_path)
    
    # Créer documents
    documents = []
    for _, row in df.iterrows():
        text = " | ".join(str(v) for v in row.values if pd.notna(v)).strip()
        if text:
            documents.append(Document(page_content=text, metadata={"source_file": file_path.name}))

    # Découper en chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = []
    for doc in documents:
        if len(doc.page_content) < CHUNK_SIZE:
            chunks.append(doc)
        else:
            chunks.extend(splitter.split_documents([doc]))
    
    # Calculer IDs des chunks
    for chunk in chunks:
        chunk.metadata["id"] = generate_chunk_id(chunk.page_content)
    
    # Charger la base Chroma existante
    embedding = OllamaEmbeddings(model=embedding_model)
    vectordb = Chroma(persist_directory=str(chroma_dir), embedding_function=embedding)
    
    # Récupérer IDs déjà indexés
    existing_ids = set(vectordb.get()['ids'])
    
    # Filtrer les chunks déjà indexés
    new_chunks = [chunk for chunk in chunks if chunk.metadata["id"] not in existing_ids]
    
    if not new_chunks:
        print("Aucun nouveau chunk à indexer.")
        return
    
    # Ajouter les nouveaux chunks à la base
    new_ids = [chunk.metadata["id"] for chunk in new_chunks]
    vectordb.add_documents(new_chunks, ids=new_ids)
    
    print(f"{len(new_chunks)} chunks ajoutés à la base.")

    
    
if __name__ == "__main__":
    # Nettoyage des données brutes vers `data/clean`
    clean_all()

    # Création de la base vectorielle dans `data/vectorstore`
    index_documents()