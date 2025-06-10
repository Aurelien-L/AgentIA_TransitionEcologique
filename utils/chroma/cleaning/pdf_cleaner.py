from pathlib import Path
from typing import List
from langchain_core.documents import Document
import fitz  # PyMuPDF
import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import polars as pl

def extract_text_from_pdf(path: Path) -> tuple[str, str] | None:
    try:
        doc = fitz.open(str(path))
        text = "\n".join(page.get_text() for page in doc)
        return path.name, text.strip()
    except Exception as e:
        print(f"❌ Extraction échouée : {path.name} - {e}")
        return None

def process_pdf_file(file: Path, out_dir: Path) -> Document | None:
    result = extract_text_from_pdf(file)
    if result and result[1]:
        file_name, text = result
        df = pl.DataFrame({"content": [text], "source": [file_name]})
        out_path = out_dir / (Path(file_name).stem + ".parquet")
        df.write_parquet(out_path)
        print(f"✅ Nettoyé : {file_name}")
        return Document(page_content=text, metadata={"source": file_name})
    return None

def clean_pdf_files(input_folder: Path, output_folder: Path) -> list[Document]:
    output_folder.mkdir(parents=True, exist_ok=True)
    pdf_files = list(input_folder.glob("*.pdf"))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda f: process_pdf_file(f, output_folder), pdf_files))

    return [doc for doc in results if doc is not None]