from pathlib import Path
from .cleaning.csv_cleaner import read_csv_files
from .cleaning.xls_cleaner import read_xls_files
from .cleaning.pdf_cleaner import clean_pdf_files

# Création du dossier 'data/clean' s'il n'existe pas déjà
chemin = Path('data') / 'clean'
chemin.mkdir(parents=True, exist_ok=True)

# Répertoires par défaut pour les fichiers bruts et nettoyés
RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")

def clean_all():
    """Nettoie tous les fichiers bruts (CSV, Excel, PDF) et les exporte en .parquet.

    Cette fonction appelle successivement les fonctions de nettoyage pour :
    - les fichiers CSV dans `data/raw/csv`
    - les fichiers Excel dans `data/raw/xls`
    - les fichiers PDF dans `data/raw/pdf`

    Les fichiers nettoyés sont ensuite enregistrés au format `.parquet` dans `data/clean`.

    Returns:
        None
    """
    print("🧹 Nettoyage des CSV...")
    csv_dfs = read_csv_files(RAW_DIR / "csv", CLEAN_DIR / "csv")

    print("🧹 Nettoyage des Excel...")
    xls_dfs = read_xls_files(RAW_DIR / "xls", CLEAN_DIR / "xls")
    
    print("🧹 Nettoyage des PDF...")
    pdf_dfs = clean_pdf_files(RAW_DIR / "pdf", CLEAN_DIR / "pdf")

    print("✅ Nettoyage terminé.")