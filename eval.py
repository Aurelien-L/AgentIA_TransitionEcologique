import random
import time
from typing import List
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

CHROMA_DIR = "chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3"  # ou mistral

TOP_K = 5  # Nombre de documents à récupérer
NUM_TESTS = 10  # Nombre d’échantillons à tester

# === Générer des questions à partir du contenu ===
def generate_questions_from_docs(docs: List[str]) -> List[tuple[str, str]]:
    llm = ChatOllama(model=LLM_MODEL)
    prompt = PromptTemplate.from_template(
        """Tu es un expert en transition écologique et en intelligence artificielle.
À partir de chaque contenu ci-dessous, génère une question pertinente liée au thème de la **transition écologique** (changements climatiques, pollution, énergies renouvelables, recyclage, développement durable, etc).

Ton objectif est de créer une question qu’une personne pourrait poser pour retrouver l’information dans ce contenu.

Conserve la structure suivante :
(question ?, résumé du contenu)

Voici les contenus :
{docs}
"""
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    combined_text = "\n\n".join([f"- {doc}" for doc in docs])
    response = chain.run({"docs": combined_text})

    # Supposons que le LLM retourne un texte structuré
    qas = []
    for line in response.split("\n"):
        if "?" in line:
            parts = line.split("?", 1)
            question = parts[0].strip() + "?"
            if len(parts) > 1:
                answer = parts[1].strip(" .:-")
                qas.append((question, answer))
    return qas


# === Évaluation de la précision ===
def evaluate_precision():
    vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL))

    all_docs = vectordb.get(include=["documents", "metadatas"])
    docs = all_docs["documents"]
    ids = all_docs["ids"]

    print(f"📄 Total de documents dans la base : {len(docs)}")

    sample = random.sample(list(zip(ids, docs)), min(NUM_TESTS, len(docs)))
    doc_texts = [doc for _, doc in sample]

    print("✍️ Génération des questions avec le LLM...")
    qas = generate_questions_from_docs(doc_texts)

    correct = 0
    total = 0

    for i, ((question, expected_content), (expected_id, _)) in enumerate(zip(qas, sample), 1):
        print(f"\n🟢 Question {i}: {question}")
        print(f"🔹 Document attendu : {expected_id}")

        results = vectordb.similarity_search(question, k=TOP_K)
        retrieved_ids = [r.metadata.get("id") or r.metadata.get("source") or "unknown" for r in results]

        print(f"🔍 Résultats retournés: {retrieved_ids}")

        if expected_id in retrieved_ids:
            correct += 1
            print("✅ Bon résultat trouvé.")
        else:
            print("❌ Pas trouvé.")

        total += 1
        time.sleep(1)  # Pour limiter les appels à Ollama

    precision = correct / total if total else 0
    print(f"\n🎯 Précision@{TOP_K} : {precision:.2f} sur {total} questions.")


if __name__ == "__main__":
    evaluate_precision()