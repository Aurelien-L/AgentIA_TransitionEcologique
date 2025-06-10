import streamlit as st

bulby = "img/mascotte.png"
bulby_mini = "img/mascotte_mini.png"
banner_bot = "img/banner_bot.png"

st.set_page_config(page_title="Bulby", layout="centered")

# col1, col2 = st.columns([0.1, 0.9], vertical_alignment="center", gap="small")
# with col1:
#     st.image(image=bulby, width=150)
# with col2:
#     st.title("*Bulby*, l’éco-assistant qui éclaire vos questions vertes ! 🌱💡")

st.image(image=banner_bot)


if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique avec avatars
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])

# Si prompt utilisateur
if prompt := st.chat_input("Votre question :"):
    # Affichage message utilisateur (pas besoin d'avatar ici)
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "avatar": None  # Ou un avatar pour l'utilisateur si tu veux
    })

    # Réponse assistant
    response = prompt
    with st.chat_message("assistant", avatar=bulby_mini):
        st.markdown(response)
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "avatar": bulby_mini
    })
