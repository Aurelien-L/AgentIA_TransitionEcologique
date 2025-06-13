# 📚 Indexation de Fichiers `.parquet` dans une Base Chroma (avec Cache et Déduplication)

## 🧠 Objectif

Indexer automatiquement des fichiers `.parquet` dans une base vectorielle [Chroma](https://www.trychroma.com/) en évitant les doublons, en découpant les textes et en loguant les embeddings.

---

## 🔧 Pourquoi ce script ?

**Contexte :**

* Des fichiers .parquet contiennent des textes issus des données nettoyé.

* L’objectif est de les rendre interrogeables de manière sémantique via une base vectorielle comme Chroma.

* Il est crucial d’éviter le recalcul des embeddings à chaque exécution : un mécanisme de cache efficace est donc mis en place pour optimiser les performances.

**Ce que fait ce code :**

| Étape            | Description                                                                |
| ---------------- | -------------------------------------------------------------------------- |
| 📁 Chargement    | Ouvre dynamiquement tous les fichiers `.parquet` dans un dossier donné     |
| 🧹 Nettoyage     | Ignore les documents vides ou invalides                                    |
| 🔀 Découpage     | Découpe les textes avec `RecursiveCharacterTextSplitter`                   |
| 🔐 Déduplication | Hash du contenu des chunks pour éviter les doublons                        |
| 🧠 Embeddings    | Utilise `OllamaEmbeddings` (ex : nomic-embed-text, llama3, etc.)           |
| 🧱 Indexation    | Envoie les chunks dans Chroma avec des IDs uniques                         |
| 💾 Cache         | Utilise un fichier `.json` pour ne pas retraiter deux fois un même fichier |

---

## 🧹 Nettoyage des fichiers bruts

Avant toute indexation, le code appelle une fonction clé : `clean_all()`, située dans `utils/chroma/run_cleaning.py`.

Cette fonction a pour rôle de préparer les données brutes provenant de différents formats (CSV, Excel, PDF) en les nettoyant, puis en les exportant au format `.parquet` dans le dossier `data/clean`.

Pour ce faire, elle utilise 3 fonctions de nettoyage spécialisées :

* [csv\_cleaner](clean_README/clean_csv.md)
* [pdf\_cleaner](clean_README/clean_pdf.md)
* [xls\_cleaner](clean_README/clean_xls.md)

### ✅ Résultat attendu

Après exécution de `clean_all()` :

Tous les fichiers bruts sont nettoyés, homogénéisés et enregistrés dans :

```bash
data/clean/csv/
data/clean/xls/
data/clean/pdf/
```

Chaque fichier nettoyé est ensuite converti au format `.parquet`, prêt à être chargé dans la base vectorielle via la fonction `index_documents()`.

---

### 🔍 Pourquoi .parquet est préféré dans ce contexte
* Format binaire ultra-rapide à lire/écrire
    * .parquet est un format colonnaire binaire compressé, contrairement à .csv ou .xls qui sont textuels.
    * Résultat : Chargement et écriture bien plus rapides (surtout pour des gros volumes).
    * Exemple : lire 10 fichiers .parquet peut être 5 à 10 fois plus rapide qu’avec des .csv.

* Compression native (snappy/zstd)
    * .parquet compresse automatiquement les données sans perte.
    * Taille des fichiers réduite de 30% à 80% par rapport aux .csv ou .xls.
    * Cela accélère aussi l’I/O (moins de données à lire depuis le disque).

* Schéma explicite et typé
    * Les .csv stockent tout en texte, donc il faut souvent parser les types à la main (int, float, datetime).
    * .parquet conserve les types de colonnes : plus sûr, plus stable, moins d’erreurs.

*  Interopérabilité & écosystème Big Data
    * .parquet est nativement supporté par Pandas, Polars, Spark, DuckDB, Dask, etc.
    * On peux facilement charger un fichier .parquet pour un traitement distribué ou vectorisé.

* Nettoyage préliminaire figé
Dans le pipeline :
    * On pars d’un .pdf ou .xls
    * On extrais et transformes le contenu en texte nettoyé
    * On le stockes une fois propre en .parquet
    * Cela permet de ne plus jamais retraiter les fichiers bruts, sauf s’ils sont modifiés.
    * On n’indexes que les .parquet, ce qui isole la partie texte utile.

#### ❌ Inconvénients des formats bruts :

|Format|Inconvénients principaux|
|---|---|
|.pdf|Non-structuré, pas adapté à l’analyse ou l’indexation directe|
|.csv|Lourd en I/O, fragile aux erreurs de format, pas typé|
|.xls(x)|Propriétaire, lent à charger, dépend de bibliothèques lourdes|

#### 🧠 Exemple dans le contexte :
Source : PDF brut = bruit, bruit visuel, sauts de ligne, erreurs d’OCR

Extraction : on nettoies → texte clair

Sauvegarde : .parquet = version "propre, lisible, rapide"

Indexation : .parquet → LangChain → chunks → Chroma

#### ✅ Résumé

|Critère|.parquet|.csv|.pdf|.xls|
|---|---|---|---|---|
Vitesse de lecture|🟢 Excellente|🔴 Faible|🔴 Très faible|🟠 Moyenne
|Compression|🟢 Native (Snappy)|🔴 Aucune|🟢 possible(PDF)|🟠 Variable|
|Support des types|🟢 Fort|🔴 Faible|🔴 Aucun|🟢 Moyen|
|Lisible par machine|🟢 Oui|🟢 Oui|🔴 Non|🟠 Oui|
|Usage dans pipeline|🟢 Idéal|🟠 Ok pour petits jeux|🔴 Prétraitement requis|🟠 Ok mais lent


## ⚖️ Pourquoi utiliser Polars et Pandas ensemble ?

<div style="text-align: center;">
    <img src="../img/polars_and_pandas.png" alt="Polars vs Pandas" width="400" />
</div>

La pipeline d’indexation repose principalement sur **Polars** pour ses performances, tout en conservant **Pandas** comme solution de repli (fallback) dans les cas plus complexes.

**Polars** est utilisé en priorité car :

* 🚀 Il est **plus rapide** que Pandas, surtout sur les gros fichiers.
* 🧠 Il utilise un traitement **colonnaire** optimisé et **multithreadé**.
* 📉 Il consomme **moins de mémoire**.

Cependant, **Pandas** est toujours utile dans les cas suivants :

* 📄 Fichiers mal formés (Excel mal encodé, CSV ambigus...).
* 🧩 Types de colonnes difficiles à inférer automatiquement.
* 🧵 Besoin de flexibilité maximale dans le parsing.

➡️ **En résumé** :

| 🐍 Lib     | Avantages                                               | Rôle dans le pipeline                   |
| ---------- | ------------------------------------------------------- | --------------------------------------- |
| **Polars** | Ultra rapide, typage strict, faible consommation        | Lecture principale et nettoyage initial |
| **Pandas** | Tolérant aux erreurs, très mature, nombreuses fonctions | Fallback si Polars échoue               |

🎯 **Bénéfice** : Cette combinaison offre le **meilleur des deux mondes** : performance et robustesse, avec une compatibilité maximale même pour des fichiers mal structurés ou issus de sources hétérogènes.

---

## 🛠️ Utilisation

### 🐍 Lancer l’indexation principale :

```bash
python chroma_db.py
```

Cela va :

* charger tous les `.parquet` dans `data/clean` (via `glob`),
* découper les textes en chunks,
* ignorer ceux déjà vus (cache JSON),
* générer les embeddings,
* indexer dans la base Chroma.

### 🔄 Mettre à jour un fichier spécifique

```python
update_file_in_index(Path("data/clean/mon_fichier.parquet"))
```

### ⚙️ Paramètres par défaut

| Variable                  | Rôle                                                  |
| ------------------------- | ----------------------------------------------------- |
| `DEFAULT_CLEAN_DIR`       | Dossier contenant les `.parquet` nettoyés             |
| `DEFAULT_CHROMA_DIR`      | Dossier où est stockée la base Chroma                 |
| `DEFAULT_EMBEDDING_MODEL` | Modèle utilisé pour vectoriser (ex: nomic-embed-text) |
| `CHUNK_SIZE`              | Longueur des morceaux de texte                        |
| `CHUNK_OVERLAP`           | Chevauchement entre deux chunks                       |
| `MAX_CHUNKS`              | Nombre maximal de chunks indexés à la fois            |
| `BATCH_SIZE_INDEX`        | Nombre de documents envoyés par batch à Chroma        |

### 📁 Cache utilisé

Le cache est stocké dans `index_cache.json`.

| Élément           | Rôle                                        |
| ----------------- | ------------------------------------------- |
| `md5 du fichier`  | Empêche de retraiter un fichier déjà indexé |
| `hash des chunks` | Évite d’avoir deux fois le même contenu     |

### 🧪 Exemple de log pour debug

```bash
✅ Loaded 5 files.
→ 'ocr_rapport_2024.parquet' : 134 chunks
✅ 127 chunks nouveaux (7 déjà indexés)
📥 Indexés en 3 batchs (batch_size=50)
```

---

## 📌 Remarques complémentaires

* Les IDs dans Chroma sont dérivés des hash de chaque chunk de texte (garantie d’unicité).
* Les documents peuvent contenir des colonnes comme `source`, `id`, etc., conservées dans les métadonnées.
* Le cache est persistant et robuste aux crashs.
* L'embeddage fonctionne avec n’importe quel modèle LangChain-compatible (`OllamaEmbeddings`, `OpenAIEmbeddings`, etc.).
