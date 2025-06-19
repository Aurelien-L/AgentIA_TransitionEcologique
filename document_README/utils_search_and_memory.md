
# 🔍 Agent RAG – Mémoire Sécurisée et Recherche Documentaire/Web

Ce module combine deux composantes essentielles d'un agent RAG basé sur LangChain :

- **SafeConversationMemory** : Une mémoire conversationnelle robuste et tolérante aux erreurs.
- **Recherche vectorielle/documentaire** via **Chroma**.
- **Recherche web** via **DuckDuckGo**.

---

## 📁 Fichiers inclus

| Fichier           | Description |
|------------------|-------------|
| `safe_memory.py` | Mémoire sécurisée pour les agents LangChain (évite les crashs en cas d'erreur d'accès). |
| `search_chroma.py` | Moteur de recherche documentaire basé sur embeddings (Ollama + Chroma) et fallback web DuckDuckGo. |

---

## 🧠 `SafeConversationMemory`

Classe héritée de `ConversationBufferMemory`, elle capture silencieusement les erreurs (corruption de fichier, IO, etc.) lors du chargement des variables mémoires.

### ✅ Avantages :
- Empêche les crashes de l’agent en production.
- Fournit une mémoire vide par défaut en cas de défaillance.

### Exemple :
```python
from safe_memory import SafeConversationMemory

memory = SafeConversationMemory(return_messages=True)
```

---

## 🧾 `search_chroma.py`

Module permettant deux types de recherches :

### 1. 🔬 **Recherche documentaire (`documentSearch`)**
- Utilise des embeddings générés avec **Ollama (`nomic-embed-text`)**.
- Recherche MMR (Max Marginal Relevance) via Chroma.
- Supprime les doublons.
- Filtre les documents par score de similarité (`threshold`).

#### Exemple :
```python
from search_chroma import documentSearch

response = documentSearch("Quels sont les effets du jeûne intermittent ?")
print(response)
```

---

### 2. 🌐 **Recherche Web (`duck_search`)**
- Interroge DuckDuckGo via `duckduckgo_search`.
- Relances automatiques en cas d’échec.
- Résultats formatés avec titre, résumé et lien.

#### Exemple :
```python
from search_chroma import duck_search

web_results = duck_search("Actualité IA open source en 2025")
print(web_results)
```

---

## ⚙️ Paramètres techniques

| Élément                  | Valeur / Description |
|--------------------------|----------------------|
| Embedding                | `nomic-embed-text` via Ollama |
| Vector Store             | Chroma (locale, persistée) |
| Score minimal (`threshold`) | 0.78 par défaut |
| Recherche Web            | DuckDuckGo, 3 tentatives, 5 résultats |

---

## 🧩 Intégration

Tu peux intégrer les fonctions `documentSearch()` et `duck_search()` comme outils d'un agent RAG LangChain, par exemple via un `Tool` ou un `Retriever`.

---

## 🛡️ Bonnes pratiques

- ✅ Utilise `SafeConversationMemory` pour éviter les erreurs silencieuses.
- ✅ Nettoie les doublons documentaires via `hashlib`.
- ✅ Prévois un fallback web (`duck_search`) en cas de silence vectoriel.

---

