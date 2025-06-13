from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import polars as pl
import pandas as pd

def clean_semantic_noise(df: pl.DataFrame) -> pl.DataFrame:
    """
    Nettoyage sémantique des colonnes texte dans un DataFrame Excel :
    - Espaces multiples
    - Retours à la ligne
    - Tabulations
    - Espaces inutiles en début/fin
    """
    for col in df.columns:
        if df.schema[col] == pl.Utf8:
            df = df.with_columns(
                pl.col(col)
                .str.replace_all(r"\s+", " ")
                .str.strip_chars()
                .alias(col)
            )
    return df

def process_excel_file(file: Path, out_dir: Path) -> pl.DataFrame | None:
    """Lit, nettoie et convertit un fichier Excel en Parquet."""
    try:
        df = pl.read_excel(file)
    except Exception:
        try:
            df_pd = pd.read_excel(file, engine="openpyxl" if file.suffix == ".xlsx" else "xlrd")
            df = pl.from_pandas(df_pd)
            print(f"⚠️ Lecture avec Pandas : {file.name}")
        except Exception as e:
            print(f"❌ Échec : {file.name} - {e}")
            return None

    if df is not None:
        df = df.with_columns(pl.all().fill_null(""))
        df = clean_semantic_noise(df)
        out_path = out_dir / (file.stem + ".parquet")
        df.write_parquet(out_path)
        print(f"✅ Excel nettoyé : {out_path.name}")
        return df
    return None

def read_xls_files(xls_dir: Path, out_dir: Path) -> list[pl.DataFrame]:
    """Nettoie tous les fichiers Excel (.xls, .xlsx) d’un dossier donné."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list(xls_dir.glob("*.xls*"))
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda f: process_excel_file(f, out_dir), files))
    return [df for df in results if df is not None]
