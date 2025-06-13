from utils.chroma.run_cleaning import clean_all
from chroma_db import index_documents
from interface.interface_functions import launch_streamlit

if __name__ == "__main__":
    # Nettoyage des données brutes vers `data/clean`
    clean_all()

    # Création de la base vectorielle dans `data/vectorstore` si elle n'existe pas déjà
    index_documents()

    # Chemin vers le fichier Streamlit
    streamlit_path = "interface/💡_Bulby.py" 

    # Lancer Streamlit
    launch_streamlit(streamlit_path)

