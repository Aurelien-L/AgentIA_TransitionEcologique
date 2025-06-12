from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import polars as pl
import pandas as pd

def fallback_read_csv(file: Path) -> pl.DataFrame | None:
    """Tente de lire un CSV avec Pandas si Polars échoue."""
    try:
        df = pd.read_csv(file, sep=",", encoding="utf-8", engine="python", error_bad_lines=False)
        print(f"⚠️ Lecture avec Pandas : {file.name}")
        return pl.from_pandas(df)
    except Exception as e:
        print(f"❌ Échec de lecture Pandas : {file.name} - {e}")
        return None

def clean_semantic_noise(df: pl.DataFrame) -> pl.DataFrame:
    """
    Supprime les bruits sémantiques des colonnes texte :
    - Espaces multiples
    - Retours à la ligne
    - Tabulations
    - Espaces inutiles en début/fin
    """
    for col in df.columns:
        if df.schema[col] == pl.Utf8:
            df = df.with_columns(
                pl.col(col)
                .str.replace_all(r"\s+", " ")  # Nettoie tous les espaces, tabs, \n
                .str.strip_chars()
                .alias(col)
            )
    return df

def process_csv_file(file: Path, out_dir: Path) -> pl.DataFrame | None:
    """Lit, nettoie et sauvegarde un fichier CSV en Parquet."""
    try:
        df = pl.read_csv(
            file,
            separator=";",
            infer_schema_length=None,
            ignore_errors=True,
            null_values=["", "NA", "n/a", "null"]
        )
    except Exception:
        df = fallback_read_csv(file)

    if df is not None:
        df = df.with_columns(pl.all().fill_null(""))  # Remplit les valeurs nulles
        df = clean_semantic_noise(df)  # Supprime les bruits sémantiques
        out_path = out_dir / (file.stem + ".parquet")
        df.write_parquet(out_path)
        print(f"✅ CSV nettoyé : {out_path.name}")
        return df
    return None

def read_csv_files(csv_dir: Path, out_dir: Path) -> list[pl.DataFrame]:
    """Lit et nettoie tous les fichiers CSV d’un dossier."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list(csv_dir.glob("*.csv"))
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda f: process_csv_file(f, out_dir), files))
    return [df for df in results if df is not None]
