import os
import uuid
import chromadb
from chromadb.api.types import QueryResult
from typing import List, Dict, Any, Optional, Sequence
from skls_embeddings.embedding_client import EmbeddingClient
from skls_embeddings.logger_config import get_logger

logger = get_logger(__name__)


class ChromaClient:
    def __init__(self, embedding_client: EmbeddingClient, path: str = os.getenv("CHROMA_PERSIST_DIR", "chroma_db"), collection_name: str = "rag_collection", logger=None):
        """
        Initializes the ChromaClient for persistent storage.

        :param embedding_client: An instance of EmbeddingClient.
        :param path: The directory path for ChromaDB's persistent storage.
        :param collection_name: The name of the collection to use.
        :param logger: Optional custom logger instance. If None, default logger will be used.
        """
        self.embedding_client = embedding_client
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.documents_collection = self.client.get_or_create_collection(name="documents_metadata")
        self.logger = logger if logger is not None else get_logger(__name__)

    def store_chunks_with_vectors(self, chunks: List[str], embeddings: Sequence[List[float]], metadatas: Sequence[Dict[str, Any]]) -> List[str]:
        """
        Stores chunked data, embeddings, and metadata in ChromaDB using unique IDs.

        :param chunks: A list of text chunks.
        :param embeddings: A list of embeddings corresponding to the chunks.
        :param metadatas: A list of metadata dictionaries for each chunk.
        :return: A list of the generated unique IDs for the stored chunks.
        """
        # print(type(embeddings).__name__)
        # print(embeddings)
        ids = [str(uuid.uuid4()) for _ in chunks]

        # Handle empty metadata dictionaries - ChromaDB validates non-empty dicts
        # Replace empty dicts with None, which ChromaDB handles correctly
        if metadatas:
            processed_metadatas = [m if m else None for m in metadatas]
        else:
            processed_metadatas = None

        self.collection.add(
            embeddings=embeddings, # type: ignore
            documents=chunks,
            metadatas=processed_metadatas, # type: ignore
            ids=ids
        )
        # print("stored chunks")
        return ids

    def store_chunk(self, text_chunk: str, metadata: Optional[Dict[str, Any]] = None, chunk_id: Optional[str] = None) -> str:
        chunk_embedding = self.embedding_client.embed_text(text_chunk)
        return self.store_chunk_with_vector(text_chunk, chunk_embedding, metadata, chunk_id)

    def store_chunk_with_vector(self, text_chunk: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None, chunk_id: Optional[str] = None) -> str:
        """
        Stores a single text chunk with its corresponding vector in ChromaDB.

        :param text_chunk: The text content to store.
        :param vector: The embedding vector corresponding to the text chunk.
        :param metadata: Optional metadata dictionary for the chunk. Will be omitted if None or empty.
        :param chunk_id: Optional ID for the chunk. If not provided, a UUID will be generated.
        :return: The ID of the stored chunk.
        """
        chunk_id = chunk_id or str(uuid.uuid4())

        # Handle metadata for ChromaDB - pass [None] instead of [{}] to avoid validation errors
        metadatas_param = [metadata] if metadata else [None]

        self.collection.add(
            embeddings=[vector],
            documents=[text_chunk],
            metadatas=metadatas_param, # type: ignore
            ids=[chunk_id]
        )

        self.logger.debug("Stored chunk with ID: %s, length: %d characters", chunk_id, len(text_chunk))
        return chunk_id

    def delete_collection(self):
        """Deletes the entire collection."""
        self.client.delete_collection(name=self.collection.name)

    def get_collection_count(self) -> int:
        """
        Returns the number of items in the collection.

        :return: The number of items in the collection.
        """
        return self.collection.count()


    def delete_chunks(self, chunk_ids: List[str]):
        """
        Deletes chunks from the collection by their IDs.

        :param chunk_ids: A list of chunk IDs to delete.
        """
        self.collection.delete(ids=chunk_ids)

    def list_collections(self) -> List[str]:
        """
        Lists all collections in the database.

        :return: A list of collection names.
        """
        return [c.name for c in self.client.list_collections()]

    def _get_collections(self):
        return [c.name for c in self.client.list_collections()]

    def delete_document(self, doc_id: str):
        """
        Deletes a document and all its associated chunks from the collections.
        """
        # Delete the document metadata
        self.documents_collection.delete(ids=[doc_id])

        # Delete all chunks associated with the document
        chunk_ids_to_delete = []
        results = self.collection.get(where={"doc_id": doc_id})
        if results and results['ids']:
            chunk_ids_to_delete.extend(results['ids'])
        
        if chunk_ids_to_delete:
            self.delete_chunks(chunk_ids_to_delete)

    def search_chunks(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches for chunks based on a query text, with an optional filter for document IDs.
        """
        query_embedding = self.embedding_client.embed_text(query_text)
        if not query_embedding:
            return []
        
        # More explicit way to define the where_clause
        where_filter = None
        self.logger.debug("Searching docs with filters: %s", where_filter)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter # type: ignore
        )
        
        formatted_results = []
        if results and results['ids'] and len(results['ids']) > 0:
            for i, chunk_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    "id": chunk_id,
                    "text": results['documents'][0][i], # type: ignore
                    "metadata": results['metadatas'][0][i], # type: ignore
                    "distance": results['distances'][0][i] # type: ignore
                })
        
        return formatted_results

    def chunk_exists(self, text: str, similarity_threshold: float = 0.95) -> bool:
        """
        Check if a chunk with similar text already exists in the collection.

        :param text: The text to check for similarity.
        :param similarity_threshold: Threshold for similarity (0-1), default 0.95 for near-exact matches.
        :return: True if a similar chunk exists, False otherwise.
        """
        # Generate embedding for the input text
        query_embedding = self.embedding_client.embed_text(text)
        if not query_embedding:
            self.logger.warning("Could not generate embedding for text: %s", text[:50] + "...")
            return False

        # Search for similar chunks in the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=1,  # Only need the most similar result
        )

        if results and results['distances'] and len(results['distances']) > 0 and results['distances'][0]:
            # ChromaDB returns cosine distances where 0 is identical and higher values mean less similarity
            # So we need to convert this to a similarity score (1 - distance) for comparison
            distance = results['distances'][0][0]
            similarity = 1 - distance  # Convert distance to similarity

            self.logger.debug("Chunk similarity check - Distance: %.3f, Similarity: %.3f, Threshold: %.3f",
                        distance, similarity, similarity_threshold)

            # Return True if similarity exceeds the threshold
            return similarity >= similarity_threshold
        else:
            # No results found, so chunk doesn't exist
            self.logger.debug("No similar chunks found for text: %s", text[:50] + "...")
            return False