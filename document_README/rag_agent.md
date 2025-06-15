# `rag_agent.py` — Agent ReAct avec recherche documentaire et web

Ce module implémente un **agent ReAct intelligent** qui combine :
- Raisonnement (Reasoning)
- Actions de recherche (Acting)
- Accès à des sources fiables (documents internes ou web)

Il respecte un ordre strict dans ses choix de source :  
**Documents → Web → IA**

## Fonctionnalités clés

- Agent LangChain basé sur `create_react_agent`
- Intégration de deux outils de recherche : documentaire (Chroma) et web (DuckDuckGo)
- Utilisation d’une mémoire conversationnelle personnalisée
- Interprétation pas à pas du raisonnement jusqu’à une réponse finale
- Mention explicite de la source utilisée : Documents, Web, IA, ou combinaison

## Classe principale : `RagAgent`

### Méthodes

| Nom | Description |
|-----|-------------|
| `__init__()` | Initialise l’agent avec outils, mémoire et LLM |
| `search(historique: list[dict])` | Lance une recherche ReAct avec les messages utilisateur/assistant |
| `historique_to_prompt(historique: list[dict])` | Transforme l’historique en texte formaté pour le modèle |

## Exemple d'utilisation

```python
from rag_agent import RagAgent

agent = RagAgent()
results = agent.search([{"role": "user", "content": "Quels sont les objectifs du plan Climat ?"}])
print(results)
```

## Dépendances

- `langchain_ollama`, `langchain.agents`, `langchain.hub`
- `SafeConversationMemory` (mémoire conversationnelle)
- Outils `documentSearch` et `duck_search` (fournis par `utils/search_chroma.py`)
