# 📄 Traitement des fichiers PDF
Le pipeline inclut également un module dédié au traitement des fichiers PDF, afin d’extraire leur contenu textuel et de le rendre exploitable pour l’indexation vectorielle.

## 🔧 Fonctionnement général

* Chaque fichier PDF est analysé pour extraire son texte intégral, page par page.
* Le texte extrait est nettoyé, encapsulé dans un Document, et sauvegardé au format .parquet.
* Le traitement est effectué en parallèle grâce à un ThreadPoolExecutor, ce qui le rend rapide même pour un grand nombre de fichiers.

## 🛠 Description des fonctions

|Fonction|Rôle|
|:--|:--|
|extract_text_from_pdf|Ouvre un PDF avec PyMuPDF (fitz) et extrait le texte de toutes les pages.|
|process_pdf_file|Nettoie et transforme un PDF en objet Document, tout en le sauvegardant au format `.parquet`|
|clean_pdf_files|Applique process_pdf_file à tous les fichiers PDF du dossier d’entrée, en parallèle.|

## ✅ Objectif

* Unifier les formats des documents en sortie (.parquet + Document).
* Automatiser le nettoyage et l'extraction.
* Assurer la traçabilité via des métadonnées (source = nom du fichier original).

## 🧠 Remarques techniques

* La librairie PyMuPDF est utilisée car elle est rapide, fiable, et offre un bon support multilingue.
* Les documents nettoyés sont prêts pour le chunking et l’indexation vectorielle dans la base Chroma utilisée plus tard dans la pipeline.