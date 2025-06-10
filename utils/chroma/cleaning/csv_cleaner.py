from concurrent.futures import ThreadPoolExecutor
import polars as pl
import pandas as pd
from pathlib import Path

def fallback_read_csv(file: Path) -> pl.DataFrame | None:
    try:
        df = pd.read_csv(file, sep=",", encoding="utf-8", engine="python", error_bad_lines=False)
        print(f"⚠️ Lecture avec Pandas pour : {file.name}")
        return pl.from_pandas(df)
    except Exception as e:
        print(f"❌ Lecture impossible même avec Pandas : {file.name} - {e}")
        return None

def process_csv_file(file: Path, out_dir: Path) -> pl.DataFrame | None:
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
    out_dir.mkdir(parents=True, exist_ok=True)
    files = list(csv_dir.glob("*.csv"))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda f: process_csv_file(f, out_dir), files))

    return [df for df in results if df is not None]