from pathlib import Path

from .cleaning.csv_cleaner import read_csv_files
from .cleaning.xls_cleaner import read_xls_files
from .cleaning.pdf_cleaner import clean_pdf_files

# Dossiers de base
RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")


def clean_all():
    """
    Lance le nettoyage de tous les types de fichiers :
    - CSV → Parquet
    - Excel → Parquet
    - PDF (page par page) → Parquet

    Les résultats sont stockés dans data/clean/[csv|xls|pdf]
    """
    print("📄 Nettoyage CSV...")
    read_csv_files(RAW_DIR / "csv", CLEAN_DIR / "csv")

    print("📊 Nettoyage Excel...")
    read_xls_files(RAW_DIR / "xls", CLEAN_DIR / "xls")

    print("📚 Nettoyage PDF...")
    clean_pdf_files(RAW_DIR / "pdf", CLEAN_DIR / "pdf")

    print("✅ Nettoyage complet terminé.")
