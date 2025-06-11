import os
import sys
import streamlit as st

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

with st.sidebar:
    "[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Aurelien-L/AgentIA_TransitionEcologique.git)"


# Affichage bannière : triche pour la centrer en ajoutant une colonne vide avant et après l'image
col1, col2, col3 = st.columns([0.15, 0.7, 0.15])

with col1:
    pass

with col2:
    st.image(image=banner_bot)

with col3:
    pass

if "chat_model" not in st.session_state:
    st.session_state.chat_model = ChatModel()

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
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "avatar": None
    })

    # Réponse assistant
    response = st.session_state.chat_model.model_response(prompt)

    with st.chat_message("assistant", avatar=bulby_mini):
        st.markdown(response)
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "avatar": bulby_mini
    })
