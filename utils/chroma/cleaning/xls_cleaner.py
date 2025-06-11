import polars as pl
import pandas as pd
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor

def process_excel_file(file: Path, out_dir: Path) -> pl.DataFrame | None:
    """Lit un fichier Excel, nettoie les données et les sauvegarde au format Parquet.

    Tente d'abord avec Polars, puis utilise Pandas en cas d'erreur.

    Args:
        file (Path): Le chemin du fichier Excel à traiter.
        out_dir (Path): Le dossier où enregistrer le fichier nettoyé.

    Returns:
        pl.DataFrame | None: Le DataFrame nettoyé ou None en cas d’échec.
    """
    try:
        df = pl.read_excel(file)
    except Exception:
        try:
            df_pd = pd.read_excel(file, engine="openpyxl" if file.suffix == ".xlsx" else "xlrd")
            df = pl.from_pandas(df_pd)
            print(f"⚠️ Lecture avec Pandas pour : {file.name}")
        except Exception as e:
            print(f"❌ Échec pour : {file.name} - {e}")
            return None

    if df is not None:
        df = df.with_columns(pl.all().fill_null(""))
        out_path = out_dir / (file.stem + ".parquet")
        df.write_parquet(out_path)
        print(f"✅ Sauvé : {out_path.name}")
        return df
    return None

def read_xls_files(xls_dir: Path, out_dir: Path) -> list[pl.DataFrame]:
    """Nettoie tous les fichiers Excel (.xls, .xlsx) d’un dossier.

    Args:
        xls_dir (Path): Le dossier contenant les fichiers Excel bruts.
        out_dir (Path): Le dossier de sortie pour les fichiers nettoyés (Parquet).

    Returns:
        list[pl.DataFrame]: Liste des DataFrames nettoyés et sauvegardés.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list(xls_dir.glob("*.xls*"))

    # Traitement en parallèle de chaque fichier
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda f: process_excel_file(f, out_dir), files))

    return [df for df in results if df is not None]