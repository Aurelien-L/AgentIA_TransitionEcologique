import pytest
from langchain.schema import Document
from langchain_chroma import Chroma
 # bien utiliser la nouvelle importation !
import shutil
import os

# Embedding factice pour tests rapides sans modèle externe
class DummyEmbedding:
    def embed_documents(self, texts):
        return [[1.0]*5 for _ in texts]
    def embed_query(self, text):
        return [1.0]*5

@pytest.fixture
def dummy_embedding():
    return DummyEmbedding()

@pytest.fixture
def sample_documents():
    return [
        Document(page_content="Transition écologique rapide", metadata={"id": "1"}),
        Document(page_content="Réduction des émissions de CO2", metadata={"id": "2"}),
        Document(page_content="Énergies renouvelables et durable", metadata={"id": "3"}),
    ]

@pytest.fixture
def chroma_persist_dir(tmp_path):
    # Chemin temporaire pour persistance Chroma
    yield tmp_path / "chroma_persist"
    # Cleanup après test
    shutil.rmtree(str(tmp_path), ignore_errors=True)

def test_index_simple(dummy_embedding, sample_documents):
    vectordb = Chroma.from_documents(
        documents=sample_documents,
        embedding=dummy_embedding,
        persist_directory=None
    )
    assert vectordb is not None

def test_similarity_search(dummy_embedding, sample_documents):
    vectordb = Chroma.from_documents(
        documents=sample_documents,
        embedding=dummy_embedding,
        persist_directory=None
    )
    results = vectordb.similarity_search("écologique")
    assert len(results) > 0
    assert any("écologique" in doc.page_content for doc in results)

def test_persistence(dummy_embedding, sample_documents, chroma_persist_dir):
    # Indexation avec persistance
    vectordb = Chroma.from_documents(
        documents=sample_documents,
        embedding=dummy_embedding,
        persist_directory=str(chroma_persist_dir)
    )
    # Stocker ID docs avant fermeture
    doc_ids_before = set(doc.metadata["id"] for doc in sample_documents)

    # Recharge Chroma à partir du dossier persistant
    vectordb_reload = Chroma(persist_directory=str(chroma_persist_dir), embedding_function=dummy_embedding)

    # Faire une recherche simple pour s’assurer que la base a bien été rechargée
    results = vectordb_reload.similarity_search("émissions")
    assert len(results) > 0

    # Vérifier qu’au moins les mêmes documents sont présents (par leurs metadata)
    found_ids = set(doc.metadata.get("id") for doc in results)
    assert doc_ids_before.intersection(found_ids)

    # Nettoyer dossier persistance
    shutil.rmtree(str(chroma_persist_dir), ignore_errors=True)