# 📚 Fonctionnement de l'interface Streamlit

## 🧠 Objectif
Permettre aux utilisateurs de dialoguer avec l’assistant via une interface web interactive, claire et fluide. Elle est développée avec **Streamlit**, une bibliothèque qui transforme du code Python en site web interactif.

---

## 🔧 `main.py` – Point d'entrée du projet

### 🧹 1. Nettoyage des données
```python
clean_all()
```
On appelle la fonction qui prépare les données en supprimant les erreurs ou en les structurant correctement, pour qu'elles soient exploitables.  
📌 **La première exécution est plus longue** car on nettoie les données brutes et on crée la base vectorielle. Les exécutions suivantes sont plus rapides.

---

### 🧠 2. Création de la base de connaissance vectorielle
```python
index_documents()
```
Bulby a besoin d'une mémoire pour chercher des infos. Cette fonction crée une **base de données vectorielle** à partir des documents du projet.

---

### 🚀 3. Lancement de l'interface utilisateur
```python
launch_streamlit(streamlit_path)
```
Lance l’interface **Streamlit**, c’est-à-dire le site web interactif où on peut discuter avec Bulby.

---

## 🧰 `interface_functions.py` – Gère Streamlit "en arrière-plan"

- `is_streamlit_running()` : Vérifie si Streamlit tourne déjà.
- `kill_streamlit_instance()` : Ferme proprement une ancienne instance si elle existe.
- `launch_streamlit()` : Relance proprement l’application.  
💡 Comme redémarrer une appli qui bug, au lieu de l’ouvrir en double.

---

## 💬 `💡_Bulby.py` – Le cœur de l'interface utilisateur

### 1. Chargement des images et paramètres de la page
```python
bulby = "img/mascotte.png"
bulby_mini = "img/mascotte_mini.png"
banner_bot = "img/banner_bot.png"
```
Chargement de la mascotte, sa version mini, et la bannière.

```python
st.set_page_config(...)
```
Définit le **titre**, l’**icône 💡** et l’**agencement large** de la page web.

---

### 2. Affichage de la bannière centrée
```python
col1, col2, col3 = st.columns([0.15, 0.7, 0.15])
with col2:
    st.image(image=banner_bot)
```
Astuce pour centrer une image dans Streamlit : on utilise 3 colonnes et on affiche au centre.

---

### 3. Initialisation de la mémoire
```python
if "chat_model" not in st.session_state:
    st.session_state.chat_model = ChatModel()
```
On charge le **modèle IA** si ce n'est pas déjà fait.

```python
if "messages" not in st.session_state:
    st.session_state.messages = []
```
Même chose pour l'**historique des messages** : on initialise une liste vide.

---

### 4. Affichage de la conversation passée
```python
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])
```
Affiche chaque message précédent avec l’avatar correspondant, comme dans un vrai chat.

---

### 5. Nouvelle question utilisateur
```python
if prompt := st.chat_input("Votre question :"):
```
Champ de saisie en bas de page. L'utilisateur écrit sa question → `prompt` contient le texte.  
ℹ️ Le `:=` permet de stocker ET tester la valeur en une ligne.

---

### 6. Affichage du message utilisateur
```python
with st.chat_message("user"):
   st.markdown(prompt)

st.session_state.messages.append({...})
```
Affiche le message et l’ajoute à l’historique.

---

### 7. Réponse de Bulby
```python
with st.chat_message("assistant", avatar=bulby_mini):
    placeholder = st.empty()
    with st.spinner("Bulby réfléchit ... 💡"):
        response = st.session_state.chat_model.model_response(prompt)
    placeholder.markdown(response)

st.session_state.messages.append({...})
```
💬 Bulby “réfléchit” (chargement), puis affiche sa réponse. Le placeholder empêche l'affichage de texte "fantôme".

---

## 🧵 En résumé visuel

| Fichier                  | Rôle                                                      |
|--------------------------|-----------------------------------------------------------|
| `main.py`                | Lance le projet complet                                   |
| `interface_functions.py` | Gère le bon lancement de l’interface                      |
| `💡_Bulby.py`            | Gère la page web : images, messages, IA                   |