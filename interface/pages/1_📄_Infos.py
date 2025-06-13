import streamlit as st

# Paramètres de la page
st.set_page_config(page_title="Informations", 
                   page_icon="📄",
                   layout="centered")

# Side bar
with st.sidebar:
    "[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Aurelien-L/AgentIA_TransitionEcologique.git)"

# Bannière
st.image("img/banner_bot.png", use_container_width=True)


# Présentation
st.header("Présentation")
st.write(
    "Ce projet à but pédagogique vise à concevoir un assistant conversationnel intelligent, "
    "capable de répondre à des questions en langage naturel sur la base de documents publics, "
    "grâce aux outils *LangChain*. Il doit combiner une chaîne RAG pour la recherche documentaire, "
    "un agent IA pour exécuter des actions via des outils personnalisés, une mémoire conversationnelle "
    "pour maintenir le contexte, et une interface utilisateur fonctionnelle développée avec *Streamlit*."
)

st.write(
    "Le projet a été réalisé par **Aurélien L.**, **Aurélien R.** et **Benjamin S.** dans le cadre de la formation "
    "*Développeur IA* chez *Simplon Hauts-de-France*."
)

st.write(
    "Nous avons créé **Bulby**, un assistant intelligent spécialisé dans la transition écologique. "
    "Il aide les citoyens à comprendre les enjeux environnementaux, les réglementations, les aides financières "
    "et les bonnes pratiques, en s’appuyant principalement sur des documents internes, puis en dernier recours "
    "sur des recherches web actualisées."
)

# Fonctionnalités principales
st.header("Fonctionnalités principales")
features = [
    "🔍 **Recherche documentaire** : Interroge une base de documents internes (lois, subventions, bonnes pratiques, etc.).",
    "🌐 **Recherche web** : Recherche d’informations à jour sur le web concernant la transition écologique.",
    "💬 **Dialogue naturel** : Réponses claires et naturelles en français.",
    "✅ **Respect de la véracité** : L’assistant ne fournit pas de réponses inventées. Si l’information n’est pas trouvée, il indique « Je ne sais pas. »"
]
for feature in features:
    st.write(feature)


# Utilisation
st.header("Utilisation")
st.write(
    "Posez vos questions sur la transition écologique. "
    "L’assistant vous répond en s’appuyant sur les sources les plus pertinentes."
)


# Auteurs + mascotte
col1, col2= st.columns([0.75, 0.25], vertical_alignment="center")

with col1:
    st.header("👤 Auteurs")
    authors = [
        "[@aruide](https://github.com/aruide)",
        "[@Aurelien-L](https://github.com/Aurelien-L)",
        "[@benjsant](https://github.com/benjsant)"
    ]
    for author in authors:
        st.write(author)

with col2:
    st.image("img/mascotte.png", use_container_width=True)
