# 📚 Indexation de Documents Structurés avec Chroma & LangChain

## 🧠 Objectif du code
Ce code vise à automatiser le nettoyage, le découpage et l’indexation de fichiers structurés (au format Parquet) dans une base vectorielle persistante (Chroma). L’objectif est de permettre une recherche sémantique efficace via des embeddings générés à l’aide du modèle nomic-embed-text.

## 🔧 Pourquoi ce code a été conçu

**Problème rencontré :**
- Les fichiers de données changent régulièrement (ajouts, corrections, etc.).
- Recalculer tous les embeddings à chaque changement serait inefficace et coûteux.
- Il fallait une solution incrémentale et robuste pour :
- Nettoyer les données,
- Générer uniquement les embeddings des nouvelles données,
- Mettre à jour la base vectorielle de manière fiable.

**Solution mise en place :**
- Cache local (`index_cache.json`) pour suivre les fichiers déjà indexés via un hash MD5.
- Détection automatique des fichiers modifiés ou nouveaux.
- Découpage intelligent des textes avec RecursiveCharacterTextSplitter.
- Déduplication par hash de contenu.
- Indexation incrémentale dans Chroma, avec gestion des IDs uniques.

## 🛠️ Fonctionnalités principales
- ✅ Nettoyage des données via `clean_all()` (modularisé dans utils/chroma/run_cleaning.py).

- 📦 Chargement dynamique des fichiers `.parquet` dans data/clean/.

- ✂️ Découpage intelligent en chunks de texte de taille contrôlée.

- 🧠 Génération d'embeddings via OllamaEmbeddings.

- 🗃️ Indexation vectorielle dans Chroma, avec persistance locale.

- ⚡ Pipeline optimisée pour éviter les doublons et les recalculs inutiles.

## 🧹 Nettoyage des fichiers bruts
Avant toute indexation, le code appelle une fonction clé : `clean_all()`, située dans utils/chroma/run_cleaning.py.

Cette fonction a pour rôle de préparer les données brutes provenant de différents formats (CSV, Excel, PDF) en les nettoyant, puis en les exportant au format .parquet dans le dossier data/clean.

Pour cela, elle s'appuie sur trois fonctions de nettoyage spécialisées :

pour ce faire il utilise 3 fonctions de  netoyage:
- [csv_cleanet](clean_README/clean_csv.md)
- [pdf_cleaner](clean_README/clean_pdf.md)
- [xls_cleaner](clean_README/clean_xls.md)

### Résultat attendu
Après exécution de `clean_all()` :

Tous les fichiers bruts sont nettoyés, homogénéisés et enregistrés dans :

```bash
data/clean/csv/
data/clean/xls/
data/clean/pdf/
```
Chaque fichier nettoyé est ensuite converti au format `.parquet`, prêt à être chargé dans la base vectorielle via la fonction index_documents().

### ⚖️ Pourquoi utiliser Polars et Pandas ensemble ?

<div style="text-align: center;">
    <img src="../img/polars_and_pandas.png" alt="Description de l'image" width="400" alignment="center">
</div>

Le projet utilise Polars comme bibliothèque principale pour le traitement des fichiers CSV, Excel et PDF convertis. Polars est plus rapide, plus léger en mémoire et hautement parallélisable par rapport à Pandas, ce qui en fait un excellent choix pour les pipelines de données intensifs.

Cependant, Polars peut se montrer strict dans certains cas de lecture :

* Encodages ambigus ou non standards.
* Détections de types incohérentes.
* Formats Excel complexes ou mal formés.

Dans ces situations, Pandas est utilisé comme solution de secours (« fallback »). Bien que moins performant, Pandas offre une tolérance plus élevée aux erreurs de structure, ce qui permet de garantir que le pipeline de nettoyage reste robuste même face à des fichiers réels souvent imparfaits.

➡️ En résumé :

* Polars est privilégié pour la performance.
* Pandas est utilisé en repli lorsqu’un fichier ne peut pas être lu proprement par Polars.
* Cela permet de bénéficier des atouts de chaque bibliothèque tout en assurant la stabilité et la fiabilité du traitement des données.

### 💾 Pourquoi convertir les fichiers en .parquet ?
Dans ce projet, les fichiers sources initiaux (.csv, .xls, et les contenus extraits des .pdf) sont convertis et enregistrés au format .parquet pour plusieurs raisons importantes :

* **Efficacité de stockage :** Le format Parquet est un format colonne compressé, ce qui réduit significativement la taille des fichiers comparé aux .csv classiques, tout en conservant toutes les informations.

* **Performance en lecture/écriture :** Parquet est optimisé pour un accès rapide aux colonnes spécifiques des données, ce qui accélère grandement les opérations de lecture, tri, filtrage et analyse, surtout sur de gros volumes.

* **Typage des données conservé :** Contrairement au CSV, Parquet conserve les types de données (entiers, flottants, dates, etc.) de manière native, évitant les erreurs ou conversions répétées lors du traitement.

* **Interopérabilité avec les outils modernes :** De nombreux outils et bibliothèques de data science (comme Polars, Pandas, Apache Spark) supportent nativement Parquet, facilitant l’intégration dans des pipelines complexes.

* **Meilleure gestion des données volumineuses :** Parquet est conçu pour gérer des datasets volumineux de manière efficace, en limitant la charge mémoire et en permettant un traitement parallèle.

En résumé, le passage au format .parquet rend le pipeline de traitement plus rapide, plus léger et plus fiable, comparé à une gestion directe des fichiers source qui peuvent être volumineux, mal formatés ou peu optimisés.

## 🚀 Exécution

```bash
python chroma_db.py
```

Cela va :
- Nettoyer les données brutes,
- Détecter les fichiers .parquet modifiés,
- Créer les embeddings,
- Mettre à jour la base Chroma de manière incrémentale.

### 🔁 Suggestion : automatisation avec CRON (optionnel)

Pour automatiser cette tâche régulièrement (par exemple, tous les jours ou toutes les semaines), il est possible d’utiliser un planificateur comme CRON.

> 💡 Cela permettrait de maintenir la base Chroma à jour automatiquement sans intervention manuelle, idéalement à des moments de faible affluence (comme tard le soir ou tôt le matin).

Exemple de ligne CRON (exécution quotidienne à 2h du matin) :
```bash
0 2 * * * /usr/bin/python3 /chemin/vers/chroma_db.py >> /chemin/vers/logs/chroma_cron.log 2>&1
```

## ⚙️ Configuration par défaut
Cette section définit les paramètres et chemins par défaut utilisés tout au long du pipeline d’indexation et de nettoyage :

|variable|description|
|:-------|:-------|
|`DEFAULT_CLEAN_DIR`|dossier où sont stockés les fichiers nettoyés et transformés (parquet notamment), issus des fichiers bruts.|
|`DEFAULT_CHROMA_DIR`|répertoire où la base de données vectorielle Chroma est persistée, pour stocker les embeddings et documents indexés.|
|`DEFAULT_EMBEDDING_MODEL`|nom du modèle d’embedding utilisé pour transformer les textes en vecteurs (ici "nomic-embed-text").|
|`CACHE_FILE`|fichier JSON qui sert à garder en mémoire les hashs des fichiers déjà traités, afin de détecter uniquement les changements et éviter un re-traitement inutile.|
|`CHUNK_SIZE`|taille maximale (en nombre de caractères) pour chaque segment de texte (chunk) découpé dans les documents.|
|`CHUNK_OVERLAP`|nombre de caractères en chevauchement entre deux chunks successifs, pour assurer une continuité contextuelle.|
|`MAX_CHUNKS`|nombre maximal de chunks à indexer dans une session, pour limiter la charge.|
|`BATCH_SIZE_INDEX`|taille des lots (batches) d’indexation envoyés à la base Chroma, pour un traitement en plusieurs passes optimisé.|

## 🔄 Mise à jour manuelle d’un seul fichier
Si on veux réindexer un fichier précis (utile en cas de mise à jour isolée) :


```python
update_file_in_index(Path("data/clean/mon_fichier.parquet"))
```

## 📌 Remarques
Le projet est conçu pour être stateless côté modèle (on changer l’embedder facilement).

La performance est optimisée par batchs (500 documents / batch) pour l’indexation.

La logique est résistante aux redémarrages grâce au cache.