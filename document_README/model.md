# `model.py` — Initialisation du modèle de chat et orchestration de l'agent

Ce module constitue le point d'entrée principal de l'application. Il initialise un modèle de langage (LLM) — DeepSeek ou LLaMA3 — et orchestre la gestion du contexte, de l'agent RAG (Recherche Augmentée) et du filtrage final des réponses.

## Fonctionnalités clés

- Chargement automatique des variables d’environnement (`.env`)
- Sélection dynamique du LLM (`DeepSeek` ou `LLaMA3`)
- Création d’un prompt système strict avec priorité : **Documents → Web → IA**
- Intégration avec l’agent RAG via la classe `RagAgent`
- Filtrage automatique des réponses pour ne conserver que :
  - La réponse finale
  - La source utilisée (IA, Documents, Web, etc.)

## Classe principale : `ChatModel`

### Méthodes

| Nom | Description |
|-----|-------------|
| `__init__()` | Initialise le modèle, la mémoire, et l’agent RAG |
| `model_response(message: str)` | Exécute le flux complet : prompt utilisateur → réponse filtrée |
| `_filter_final_answer_and_source(text: str)` | Extrait proprement la réponse finale et sa source du raisonnement complet |

## Exemple d’utilisation

```python
chat = ChatModel()
response = chat.model_response("Quels sont les objectifs du plan Climat de la France ?")
print(response)
```

## Dépendances

- `langchain_deepseek`
- `langchain_ollama`
- `langchain_core`
- `dotenv`
- `rag_agent.RagAgent`
