import streamlit as st


col1, col2 = st.columns([0.2, 0.8], vertical_alignment="center", gap="medium")

with col1:
    st.image(image="img/mascotte.png")

with col2:
    st.title("Cap'tain Planet, le ChatBot le + vert !")

    
if "messages" not in st.session_state:
    st.session_state.messages =  []
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
if prompt := st.chat_input("Votre question au Cap'tain :"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role" : "user", "content": prompt})
    response = f"Le Cap'tain répète : {prompt}"
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})