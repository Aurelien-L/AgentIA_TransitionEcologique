import pytest
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import FakeEmbeddings  # Correct import

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.chains import RetrievalQA


@pytest.fixture
def sample_docs():
    return [
        Document(page_content="La transition écologique vise à réduire les émissions de CO2.", metadata={"source": "doc1"}),
        Document(page_content="L'énergie renouvelable est un élément clé pour un futur durable.", metadata={"source": "doc2"}),
        Document(page_content="La réduction de la consommation d'énergie est essentielle pour lutter contre le changement climatique.", metadata={"source": "doc3"}),
    ]

def test_functional_qa_search(sample_docs, tmp_path):
    embedding = FakeEmbeddings(model_name="fake", size=1536)  # modèle factice pour test

    vectordb = Chroma.from_documents(
        documents=sample_docs,
        embedding=embedding,
        persist_directory=str(tmp_path)
    )

    query = "Comment réduire les émissions de gaz à effet de serre ?"
    results = vectordb.similarity_search(query, k=2)
    returned_texts = [doc.page_content for doc in results]

    assert any("émissions" in text or "transition écologique" in text for text in returned_texts), \
        "La recherche ne retourne pas de documents pertinents."
        

@pytest.fixture
def sample_docs():
    return [
        Document(page_content="La transition écologique vise à réduire les émissions de CO2.", metadata={"source": "doc1"}),
        Document(page_content="La réduction de la consommation d'énergie est essentielle pour lutter contre le changement climatique.", metadata={"source": "doc2"}),
    ]

def test_ollama_agent_qa(tmp_path, sample_docs):
    # 1. Embeddings Ollama
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # 2. Indexer dans Chroma (persist_directory temporaire)
    vectordb = Chroma.from_documents(sample_docs, embedding=embeddings, persist_directory=str(tmp_path))

    # 3. Créer LLM Ollama
    llm = ChatOllama(model="llama3")

    # 4. Chaîne RetrievalQA (agent question/réponse)
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())

    # 5. Question connue
    question = "Quel est l'objectif principal de la transition écologique ?"

    # 6. Obtenir la réponse
    answer = qa_chain.run(question)

    print("Réponse:", answer)

    # 7. Assert sur contenu attendu (en minuscule pour robustesse)
    assert "réduire les émissions" in answer.lower()

    # Nettoyer la base
    vectordb.persist()
    vectordb.delete()