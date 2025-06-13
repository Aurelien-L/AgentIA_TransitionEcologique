# 📁 Traitement des fichiers CSV
Lors du nettoyage, les fichiers .csv sont traités par la fonction read_csv_files().
Elle automatise la lecture, le nettoyage sémantique, le remplissage des champs manquants, et la conversion au format Parquet pour chaque fichier trouvé dans un dossier donné.

## 🔧 Fonctionnement général
Les fichiers sont lus en parallèle grâce à ThreadPoolExecutor pour un traitement rapide.

Chaque fichier .csv est soumis au processus suivant :

* 📥 Lecture initiale avec Polars (; comme séparateur).

* 🛟 Fallback automatique via Pandas si Polars échoue (encodage, structure défectueuse, etc.).

* 🧹 Nettoyage sémantique :

    * Suppression des espaces multiples
    * Nettoyage des tabulations, sauts de ligne, etc.
    * Trim des chaînes (.strip()).

* 🕳️ Remplissage des champs vides (null ➜ "").

* 💾 Conversion et export du fichier au format .parquet.

Un message clair avec emoji est affiché à chaque étape importante pour suivre le traitement.

## 🛠 Résumé des fonctions principales
|Fonction|	Rôle|
|---|---|
|fallback_read_csv|	Tente une lecture via Pandas si Polars échoue.|
|clean_semantic_noise|	Supprime les bruits dans les colonnes texte (espaces, tab, etc.).|
|process_csv_file|	Lit, nettoie et convertit un fichier CSV en .parquet.|
|read_csv_files|	Applique process_csv_file à tous les fichiers d’un dossier.|

## ✅ Avantages de cette approche
- Robuste : même les fichiers mal formatés sont pris en charge grâce au fallback Pandas.
- Performant : traitement parallélisé pour des milliers de fichiers en un minimum de temps.
- Standardisé : production homogène de fichiers .parquet, parfaits pour l’analyse ou l’indexation vectorielle.
- Lisible : les logs avec emojis facilitent le debug et la supervision.