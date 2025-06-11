from concurrent.futures import ThreadPoolExecutor
import polars as pl
import pandas as pd
from pathlib import Path

def fallback_read_csv(file: Path) -> pl.DataFrame | None:
    """Tente de lire un fichier CSV avec pandas si Polars échoue.

    Args:
        file (Path): Le chemin vers le fichier CSV à lire.

    Returns:
        pl.DataFrame | None: Le DataFrame Polars si la lecture réussit, sinon None.
    """
    try:
        df = pd.read_csv(file, sep=",", encoding="utf-8", engine="python", error_bad_lines=False)
        print(f"⚠️ Lecture avec Pandas pour : {file.name}")
        return pl.from_pandas(df)
    except Exception as e:
        print(f"❌ Lecture impossible même avec Pandas : {file.name} - {e}")
        return None

def process_csv_file(file: Path, out_dir: Path) -> pl.DataFrame | None:
    """Lit, nettoie et convertit un fichier CSV en Parquet à l'aide de Polars.

    Si la lecture avec Polars échoue, un fallback avec pandas est tenté.

    Args:
        file (Path): Le chemin du fichier CSV à traiter.
        out_dir (Path): Le dossier de sortie pour les fichiers Parquet.

    Returns:
        pl.DataFrame | None: Le DataFrame traité, ou None si la lecture échoue.
    """
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
        df = df.with_columns(pl.all().fill_null(""))
        out_path = out_dir / (file.stem + ".parquet")
        df.write_parquet(out_path)
        print(f"✅ Sauvé : {out_path.name}")
        return df
    return None

def read_csv_files(csv_dir: Path, out_dir: Path) -> list[pl.DataFrame]:
    """Traite tous les fichiers CSV d'un dossier donné et les convertit en Parquet.

    Utilise un pool de threads pour paralléliser le traitement des fichiers.

    Args:
        csv_dir (Path): Dossier contenant les fichiers CSV bruts.
        out_dir (Path): Dossier dans lequel sauvegarder les fichiers Parquet nettoyés.

    Returns:
        list[pl.DataFrame]: Liste des DataFrames nettoyés et convertis.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list(csv_dir.glob("*.csv"))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda f: process_csv_file(f, out_dir), files))

    return [df for df in results if df is not None]