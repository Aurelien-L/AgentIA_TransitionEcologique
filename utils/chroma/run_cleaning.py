from pathlib import Path
from .cleaning.csv_cleaner import read_csv_files
from .cleaning.xls_cleaner import read_xls_files
from .cleaning.pdf_cleaner import clean_pdf_files

RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")

def clean_all():
    print("🧹 Nettoyage des CSV...")
    csv_dfs = read_csv_files(RAW_DIR / "csv", CLEAN_DIR / "csv")

    print("🧹 Nettoyage des Excel...")
    xls_dfs = read_xls_files(RAW_DIR / "xls", CLEAN_DIR / "xls")
    
    print("🧹 Nettoyage des PDF...")
    pdf_dfs = clean_pdf_files(RAW_DIR / "pdf", CLEAN_DIR / "pdf")

    print("✅ Nettoyage terminé.")