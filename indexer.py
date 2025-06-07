import hashlib
import time
import json
from pathlib import Path
import pandas as pd

from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# === CONFIGURATION PAR DÉFAUT ===
CLEAN_DIR = Path("data/clean")
CHROMA_DIR = Path("chroma_db")
EMBEDDING_MODEL = "nomic-embed-text"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
MAX_CHUNKS = 1000
BATCH_SIZE_INDEX = 500


# === UTILS ===
def log_time(label: str, start: float):
    print(f"⏱️ {label}: {time.time() - start:.2f}s")

def generate_chunk_id(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_parquet_documents(clean_dir: Path) -> list[Document]:
    documents = []
    for file in clean_dir.rglob("*.parquet"):
        df = pd.read_parquet(file)
        for _, row in df.iterrows():
            text = " | ".join(str(value) for value in row.values if pd.notna(value)).strip()
            if text:
                documents.append(Document(
                    page_content=text,
                    metadata={"s": file.name[:12]}
                ))
    return documents

def get_existing_ids(chroma_dir: Path) -> set[str]:
    if not chroma_dir.exists():
        return set()
    try:
        db = Chroma(persist_directory=str(chroma_dir), embedding_function=None)
        return set(db.get()['ids'])
    except Exception:
        return set()


# === PIPELINE PRINCIPAL ===
def index_documents(
    clean_dir: Path = CLEAN_DIR,
    chroma_dir: Path = CHROMA_DIR,
    embedding_model: str = EMBEDDING_MODEL,
    embedding=None,
) -> dict | None:
    global_start = time.time()

    print("📥 Chargement des fichiers .parquet...")
    start = time.time()
    raw_docs = load_parquet_documents(clean_dir)
    log_time("Chargement", start)
    print(f"✅ {len(raw_docs)} documents bruts.")

    if not raw_docs:
        print("⚠️ Aucun document trouvé.")
        return None

    print("🧹 Déduplication...")
    start = time.time()
    seen = set()
    unique_docs = []
    for doc in raw_docs:
        h = generate_chunk_id(doc.page_content)
        if h not in seen:
            seen.add(h)
            unique_docs.append(doc)
    log_time("Déduplication", start)
    print(f"✅ {len(unique_docs)} documents uniques.")

    print("🔪 Découpage en chunks...")
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

    print("🆔 Attribution des IDs...")
    for chunk in chunks:
        chunk.metadata["id"] = generate_chunk_id(chunk.page_content)

    id_mapping = {chunk.metadata["id"]: chunk.page_content for chunk in chunks}
    with open("mapping_ids.json", "w", encoding="utf-8") as f:
        json.dump(id_mapping, f, indent=2, ensure_ascii=False)

    print("📂 Récupération des IDs déjà indexés...")
    existing_ids = get_existing_ids(chroma_dir)
    new_chunks = [c for c in chunks if c.metadata["id"] not in existing_ids]
    print(f"🆕 {len(new_chunks)} chunks à indexer.")

    if not new_chunks:
        print("✅ Aucun nouveau chunk à indexer.")
        return {
            "raw_docs": len(raw_docs),
            "unique_docs": len(unique_docs),
            "chunks": len(chunks),
            "indexed": 0,
        }

    new_chunks = new_chunks[:MAX_CHUNKS]

    print("🧠 Indexation dans Chroma (batch)...")
    start = time.time()
    embedding = embedding or OllamaEmbeddings(model=embedding_model)
    vectordb = None
    total = len(new_chunks)
    batches = [new_chunks[i:i + BATCH_SIZE_INDEX] for i in range(0, total, BATCH_SIZE_INDEX)]

    for i, batch in enumerate(batches, 1):
        batch_start = time.time()
        try:
            if vectordb is None:
                vectordb = Chroma.from_documents(
                    documents=batch,
                    embedding=embedding,
                    persist_directory=str(chroma_dir)
                )
            else:
                vectordb.add_documents(batch)
            elapsed = time.time() - batch_start
            remaining = (len(batches) - i) * elapsed
            print(f"✅ Batch {i}/{len(batches)} indexé. ⏱️ Temps estimé restant : {remaining:.1f}s")
        except Exception as e:
            print(f"❌ Erreur batch {i}: {e}")

    log_time("⏳ Pipeline complet", global_start)
    print("✅ Chroma mise à jour avec succès.")

    return {
        "raw_docs": len(raw_docs),
        "unique_docs": len(unique_docs),
        "chunks": len(chunks),
        "indexed": len(new_chunks),
    }