import polars as pl
import pandas as pd
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor

def process_excel_file(file: Path, out_dir: Path) -> pl.DataFrame | None:
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
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list(xls_dir.glob("*.xls*"))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda f: process_excel_file(f, out_dir), files))

    return [df for df in results if df is not None]