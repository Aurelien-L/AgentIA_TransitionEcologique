# 🗂 Traitement des fichiers CSV
Lors du nettoyage, les fichiers .csv sont traités par la fonction read_csv_files(). Elle automatise la lecture, le nettoyage, et la conversion au format Parquet pour chaque fichier CSV trouvé dans un dossier donné.

## 🔧 Fonctionnement général
Les fichiers sont lus en parallèle pour accélérer le traitement grâce à un ThreadPoolExecutor.

Chaque fichier est :
* Ouvert avec la bibliothèque Polars, très rapide pour la lecture tabulaire.
* Si Polars échoue (fichier mal formé), une lecture de secours est tentée avec Pandas.
* Les données sont nettoyées : valeurs null remplacées par "".
* Le fichier nettoyé est sauvegardé au format .parquet dans un dossier de sortie.

## 🛠 Résumé des fonctions principales
Fonction	Rôle

|Fonction|Rôle|
|:--|:--|
|fallback_read_csv|Tente une lecture via Pandas si Polars échoue.|
|process_csv_file|Nettoie un fichier CSV et le convertit en Parquet.|
|read_csv_files|Applique process_csv_file à tous les fichiers .csv en parallèle.|

## ✅ Avantages de cette approche

* Robuste : même les fichiers problématiques sont traités grâce au fallback Pandas.
* Performant : le parallélisme réduit fortement le temps de traitement si de nombreux fichiers sont présents.
* Standardisé : tous les fichiers sont convertis au même format (.parquet), facilitant l’indexation vectorielle ensuite.