from utils.chroma.run_cleaning import clean_all
from chroma_db import index_documents, update_file_in_index
from pathlib import Path

if __name__ == "__main__":
    # Nettoyage des données brutes vers `data/clean`
    clean_all()

    # Création de la base vectorielle dans `data/vectorstore`
    index_documents()
