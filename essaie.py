from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence


# 📌 Paramètres
persist_directory = "./chroma_db"

# 🔧 Embedding + LLM
embedding_model = OllamaEmbeddings(model="nomic-embed-text")
llm = ChatOllama(model="llama3", temperature=0)

# 📚 Base vectorielle
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)

# ✍️ Prompt template
prompt_template = """
Tu es un assistant qui crée une question simple, claire et pertinente liée à la transition écologique, basée sur le contenu suivant :

Contenu :
{content}

Question :
"""
prompt = PromptTemplate.from_template(prompt_template)

# 🚀 Chaîne avec nouveau système `Runnable`
chain = prompt | llm

# 📥 Chargement des documents
all_docs = vectordb._collection.get(include=["metadatas", "documents"])
documents = all_docs["documents"]
metadatas = all_docs["metadatas"]

print("NB DOCUMENT:")
print(f"Nombre de documents dans la base : {len(documents)}")

# 🎯 Génération des paires (question -> ID attendu)
test_data = []
for doc_content, metadata in zip(documents[:20], metadatas[:20]):
    question = chain.invoke({"content": doc_content}).content.strip().split('\n')[0]
    expected_id = metadata.get("id")
    test_data.append((question, [expected_id]))

# 🔍 Évaluation de la précision@k
def precision_at_k(test_data, vectordb, k=5):
    total = len(test_data)
    hits = 0

    for i, (question, expected_ids) in enumerate(test_data, 1):
        results = vectordb.similarity_search(question, k=k)
        retrieved_ids = [doc.metadata.get("id") for doc in results]

        found = any(eid in retrieved_ids for eid in expected_ids)

        print(f"Question {i}: {question}")
        print(f"Attendu : {expected_ids}")
        print(f"Retrouvé : {retrieved_ids}")
        print("✅ Trouvé." if found else "❌ Pas trouvé.")
        print("")

        if found:
            hits += 1

    precision = hits / total if total > 0 else 0
    print(f"🎯 Précision moyenne@{k} : {precision:.2f} sur {total} questions.")
    return precision

precision_at_k(test_data, vectordb, k=5)