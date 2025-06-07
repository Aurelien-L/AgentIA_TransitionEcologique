import pytest
from unittest.mock import patch, MagicMock
from langchain.schema import Document
from indexer import index_documents

@pytest.fixture
def fake_documents():
    return [
        Document(metadata={'s': 'test1'}, page_content='Transition écologique et réduction des émissions de CO2 à grande échelle.'),
        Document(metadata={'s': 'test2'}, page_content='Transition écologique vers la neutralité carbone pour 2050, avec des mesures concrètes.'),
        Document(metadata={'s': 'test3'}, page_content='Transition écologique et réduction des émissions de CO2 à grande échelle.'),
    ]

@patch("indexer.load_parquet_documents")
@patch("indexer.OllamaEmbeddings")
@patch("indexer.Chroma")
def test_index_documents_basic(mock_chroma_class, mock_embedding_class, mock_loader, fake_documents):
    # Setup mocks
    mock_loader.return_value = fake_documents
    mock_embedding = MagicMock()
    mock_embedding_class.return_value = mock_embedding
    
    mock_chroma = MagicMock()
    mock_chroma_class.from_documents.return_value = mock_chroma
    
    # Appel de la fonction index_documents
    result = index_documents()

    # Assertions sur les résultats
    assert result["raw_docs"] == 3
    assert result["unique_docs"] == 2      # 1 doublon filtré
    assert result["chunks"] >= 2           # au moins 2 chunks générés

    # Vérifier que add_documents n'a pas été appelé (tout indexé en 1 batch)
    mock_chroma.add_documents.assert_not_called()
    mock_chroma_class.from_documents.assert_called_once()