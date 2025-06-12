from pathlib import Path
from typing import List
from langchain_core.documents import Document
import fitz  # PyMuPDF
import polars as pl
from concurrent.futures import ThreadPoolExecutor
import re


def clean_text(text: str) -> str:
    """
    Nettoie le texte brut extrait d'un PDF :
    - Supprime les espaces multiples, tabulations, sauts de ligne redondants
    - Nettoie les débuts/fins de lignes
    """
    text = re.sub(r"\s+", " ", text)  # Remplace tout type d'espace par un espace simple
    return text.strip()


def extract_text_from_pdf(path: Path) -> List[tuple[str, str]]:
    """
    Extrait le texte page par page d’un PDF et nettoie chaque page.

    Args:
        path (Path): Chemin du fichier PDF

    Returns:
        List[tuple[str, str]]: Liste des (nom, texte) pour chaque page
    """
    try:
        doc = fitz.open(str(path))
        return [
            (f"{path.name}_page_{i+1}", clean_text(page.get_text()))
            for i, page in enumerate(doc)
        ]
    except Exception as e:
        print(f"❌ Erreur d'extraction PDF : {path.name} - {e}")
        return []


def process_pdf_file(file: Path, out_dir: Path) -> List[Document]:
    """
    Traite un fichier PDF, extrait les pages, nettoie, sauvegarde en parquet.

    Args:
        file (Path): Fichier PDF à traiter
        out_dir (Path): Dossier de sortie .parquet

    Returns:
        List[Document]: Liste de documents LangChain nettoyés
    """
    page_data = extract_text_from_pdf(file)
    documents = []

    for page_id, text in page_data:
        if text.strip():
            df = pl.DataFrame({"content": [text], "source": [page_id]})
            out_path = out_dir / f"{page_id}.parquet"
            df.write_parquet(out_path)
            print(f"✅ PDF nettoyé : {page_id}")
            documents.append(Document(page_content=text, metadata={"source": page_id}))

    return documents


def clean_pdf_files(input_folder: Path, output_folder: Path) -> List[Document]:
    """
    Nettoie tous les fichiers PDF d’un dossier.

    Args:
        input_folder (Path): Dossier d’entrée
        output_folder (Path): Dossier de sortie

    Returns:
        List[Document]: Liste de tous les documents PDF nettoyés
    """
    output_folder.mkdir(parents=True, exist_ok=True)
    pdf_files = list(input_folder.glob("*.pdf"))

    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda f: process_pdf_file(f, output_folder), pdf_files)

    # Fusionne les listes de pages nettoyées
    return [doc for sublist in results for doc in sublist]
