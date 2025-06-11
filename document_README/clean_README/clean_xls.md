# 📊 Traitement des fichiers Excel (.xls, .xlsx)
Le projet intègre un pipeline de nettoyage pour les fichiers Excel, visant à les transformer en un format structuré et exploitable (au format .parquet).

## 🔧 Fonctionnement général
Les fichiers .xls et .xlsx sont lus à l’aide de Polars, avec une tentative de repli via Pandas si nécessaire.

Les cellules vides sont remplies par défaut pour assurer une uniformité des colonnes.

Chaque fichier nettoyé est sauvegardé en .parquet dans un répertoire de sortie.

## 🛠 Description des fonctions

|Fonction|Rôle|
|:--|:--|
|`process_excel_file`|Tente de lire un fichier Excel avec Polars, sinon Pandas. Nettoie les données et les enregistre.|
|`read_xls_files`|Applique process_excel_file à tous les fichiers Excel d’un dossier donné, en parallèle.|

## ✅ Objectifs

* Garantir la robustesse de la lecture (grâce au fallback Pandas si Polars échoue).
* Nettoyer et homogénéiser les données provenant de fichiers Excel hétérogènes.
* Optimiser la performance via du traitement parallèle (multithreading avec ThreadPoolExecutor).

## 🧠 Remarques techniques

* Le repli automatique vers Pandas permet de gérer les fichiers problématiques qui ne peuvent pas être lus directement par Polars.
* Le format .parquet est choisi pour sa compacité, sa vitesse d'accès, et sa compatibilité avec les outils de traitement de données.
* Les fichiers transformés sont ensuite utilisés dans la phase d’indexation vectorielle.

