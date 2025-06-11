import streamlit as st

# Paramètres de la page
st.set_page_config(page_title="Credits", 
                   page_icon="📜",
                   layout="centered")

# Side bar
with st.sidebar:
    "[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Aurelien-L/AgentIA_TransitionEcologique.git)"


# Contenu
st.caption("*Projet réalisé par __Aurélien Leva__, __Aurélien Ruide__ et __Benjamin Santrisse__ dans le cadre d'un projet pédagogique pour la formation __Développeur IA__ chez __Simplon Hauts-de-France__.*")
