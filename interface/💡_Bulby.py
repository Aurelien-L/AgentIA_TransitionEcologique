import streamlit as st
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.model import ChatModel


# Import images
bulby = "img/mascotte.png"
bulby_mini = "img/mascotte_mini.png"
banner_bot = "img/banner_bot.png"


# Paramètres page
st.set_page_config(page_title="Bulby", 
                   page_icon="💡",
                   layout="wide")

# Sidebar
with st.sidebar:
    "[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Aurelien-L/AgentIA_TransitionEcologique.git)"



# Affichage bannière : triche pour la centrer en ajoutant une colonne vide avant et après l'image
col1, col2, col3 = st.columns([0.15, 0.7, 0.15])
with col2:
    st.image(image=banner_bot)


# Si modèle n'est pas encore stocké dans la session, on le sauvegarde pour le conserver
if "chat_model" not in st.session_state:
    st.session_state.chat_model = ChatModel()

# Si historique des messages n'existe pas encore, on initialise une liste vide pour le stocker
if "messages" not in st.session_state:
    st.session_state.messages = []


# Affichage de l'historique avec avatars
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])


# Si prompt utilisateur
if prompt := st.chat_input("Votre question :"):


    # Affichage message utilisateur
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ajout message utilisateur dans l'historique
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "avatar": None
    })


    # Réponse assistant
    with st.chat_message("assistant", avatar=bulby_mini):
        placeholder = st.empty()  # permet d'éviter un problème de réponse fantôme
        with st.spinner("Bulby réfléchit ... 💡"):
            response = st.session_state.chat_model.model_response(prompt)
        placeholder.markdown(response)

    # Ajout réponse assistant dans l'historique
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "avatar": bulby_mini
    })

    st.stop()
