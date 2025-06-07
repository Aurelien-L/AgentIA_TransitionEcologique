import pytest
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.chains import RetrievalQA
import random

def test_chroma_real_search_random_questions():
    persist_dir = "chroma_db"  # adapte selon ta config
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    llm = ChatOllama(model="llama3")
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())

    questions = [
        "Quels sont les objectifs de la transition écologique ?",
        "Comment réduire la consommation d'énergie dans l'industrie ?",
        "Quels sont les principaux gaz à effet de serre ?",
        "Quels sont les bénéfices du recyclage ?",
        "Comment favoriser l'économie circulaire ?"
    ]

    question = random.choice(questions)

    raw_response = qa_chain.invoke(question)

    # Extraire la vraie réponse si la réponse est un dict
    if isinstance(raw_response, dict) and "result" in raw_response:
        answer = raw_response["result"]
    else:
        answer = raw_response

    print(f"Question: {question}\nRéponse: {answer}")

    assert isinstance(answer, str)
    assert len(answer.strip()) > 10

    keywords = ["écologique", "énergie", "réduction", "gaz", "recyclage", "circulaire"]
    assert any(keyword in answer.lower() for keyword in keywords), "La réponse semble hors sujet"