from pathlib import Path
from typing import List
from langchain_core.documents import Document
import fitz  # PyMuPDF
import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import polars as pl

def extract_text_from_pdf(path: Path) -> tuple[str, str] | None:
    """Extrait le texte d'un fichier PDF.

    Args:
        path (Path): Le chemin du fichier PDF à lire.

    Returns:
        tuple[str, str] | None: Un tuple contenant le nom du fichier et son contenu texte,
        ou None si l'extraction échoue.
    """
    try:
        doc = fitz.open(str(path))
        text = "\n".join(page.get_text() for page in doc)
        return path.name, text.strip()
    except Exception as e:
        print(f"❌ Extraction échouée : {path.name} - {e}")
        return None

def process_pdf_file(file: Path, out_dir: Path) -> Document | None:
    """Nettoie un fichier PDF en extrayant le texte et en sauvegardant le résultat en Parquet.

    Args:
        file (Path): Le chemin du fichier PDF à traiter.
        out_dir (Path): Le dossier de sortie pour sauvegarder le fichier nettoyé.

    Returns:
        Document | None: Un objet Document avec le contenu et les métadonnées, ou None si échec.
    """
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
    """Nettoie tous les fichiers PDF dans un dossier donné.

    Chaque PDF est lu, converti en texte, sauvegardé en Parquet, et transformé en objet Document.

    Args:
        input_folder (Path): Dossier contenant les fichiers PDF bruts.
        output_folder (Path): Dossier où sauvegarder les fichiers nettoyés.

    Returns:
        list[Document]: Liste des documents nettoyés avec texte et métadonnées.
    """
    output_folder.mkdir(parents=True, exist_ok=True)
    pdf_files = list(input_folder.glob("*.pdf"))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda f: process_pdf_file(f, output_folder), pdf_files))

    return [doc for doc in results if doc is not None]