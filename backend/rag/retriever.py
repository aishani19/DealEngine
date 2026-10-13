import logging
from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.rag.document_store import DocumentStore, DocumentChunk
from backend.models import Citation
from backend.config import settings

logger = logging.getLogger(__name__)


class RAGRetriever:
    _instance = None

    def __init__(self):
        self.doc_store = DocumentStore()
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_df=0.95,
            min_df=1
        )
        self.doc_matrix = None
        self._build_index()

    @classmethod
    def get_instance(cls) -> "RAGRetriever":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _build_index(self):
        """Builds TF-IDF vector space index over all document chunks."""
        if not self.doc_store.chunks:
            logger.warning("No chunks available to index in DocumentStore.")
            return

        corpus = [chunk.text for chunk in self.doc_store.chunks]
        self.doc_matrix = self.vectorizer.fit_transform(corpus)
        logger.info(f"Vector index built with {self.doc_matrix.shape[0]} documents and {self.doc_matrix.shape[1]} features.")

    def retrieve(self, query: str, top_k: int = None, min_score: float = None) -> List[Tuple[DocumentChunk, float]]:
        """
        Retrieves top_k most semantically relevant chunks for a user query.
        Returns list of (DocumentChunk, score)
        """
        if top_k is None:
            top_k = settings.TOP_K_RETRIEVAL
        if min_score is None:
            min_score = settings.SIMILARITY_THRESHOLD

        if self.doc_matrix is None or not self.doc_store.chunks:
            return []

        # Vectorize query
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.doc_matrix).flatten()

        # Get top-k indices sorted descending
        ranked_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            # Even if score is low, guarantee at least top 1 result if score > 0.05
            if score >= min_score or (len(results) == 0 and score > 0.05):
                results.append((self.doc_store.chunks[idx], round(score, 4)))

        return results

    def retrieve_citations(self, query: str, top_k: int = 3) -> List[Citation]:
        """Convenience method returning Pydantic Citation models."""
        matches = self.retrieve(query, top_k=top_k)
        citations = []
        for chunk, score in matches:
            # Build a crisp snippet (first 250 chars)
            snippet = chunk.text[:280].strip() + ("..." if len(chunk.text) > 280 else "")
            citations.append(Citation(
                source_title=chunk.title,
                source_file=chunk.source_file,
                section=chunk.section,
                relevance_score=score,
                snippet=snippet
            ))
        return citations

    def get_index_stats(self) -> dict:
        """Returns metadata about the currently indexed knowledge base."""
        return {
            "total_chunks": len(self.doc_store.chunks),
            "sources": sorted(list(set(c.source_file for c in self.doc_store.chunks))),
            "vocabulary_size": len(self.vectorizer.vocabulary_) if hasattr(self.vectorizer, "vocabulary_") else 0,
            "vector_dimension": self.doc_matrix.shape[1] if self.doc_matrix is not None else 0
        }
