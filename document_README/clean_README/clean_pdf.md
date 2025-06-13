# 📁 Traitement des fichiers PDF
Lors du nettoyage, les fichiers .pdf sont traités par la fonction clean_pdf_files().
Elle automatise l'extraction du texte par page, le nettoyage, et la sauvegarde de chaque page au format Parquet, tout en construisant des objets Document exploitables par LangChain.

## 🔧 Fonctionnement général
Les fichiers PDF sont traités en parallèle via un ThreadPoolExecutor pour améliorer la vitesse.

Chaque fichier PDF est soumis au pipeline suivant :

* 📄 Lecture page par page avec PyMuPDF (fitz).

* 🧹 Nettoyage du texte :

    * Suppression des espaces multiples, tabulations, retours à la ligne superflus.
    * Trim du contenu.

* 💾 Sauvegarde au format .parquet : une page ➜ un fichier.

* 📦 Création d’un objet LangChain.Document pour chaque page, avec le texte et la source.

Chaque étape est journalisée avec des emojis pour un suivi visuel clair.

## 🛠 Résumé des fonctions principales
|Fonction|	Rôle|
|---|---|
|clean_text|	Nettoie le texte extrait (espaces, retours, trim).|
|extract_text_from_pdf|	Extrait et nettoie le texte page par page d’un PDF.|
|process_pdf_file|	Gère l’extraction et la sauvegarde d’un fichier PDF complet.|
|clean_pdf_files|	Applique process_pdf_file à tous les PDF d’un dossier.|

## ✅ Avantages de cette approche

* Granulaire : chaque page est traitée séparément (utile pour la recherche sémantique).

* Interopérable : conversion directe vers le format .parquet + création d’objets Document pour LangChain.

* Performant : le traitement est parallélisé pour traiter plusieurs PDF rapidement.

* Fiable : les erreurs d’extraction sont loguées, mais ne bloquent pas l’ensemble du traitement.