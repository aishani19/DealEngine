import pytest
from backend.rag.retriever import RAGRetriever
from backend.rag.document_store import DocumentStore


def test_document_store_loads_chunks():
    store = DocumentStore()
    assert len(store.chunks) > 0
    # Check that core services, products, and case studies are present
    titles = [c.title for c in store.chunks]
    assert any("AI Automation" in t or "Autonomous" in t or "Service" in t for t in titles)
    assert any("TenantEase" in t for t in titles)
    assert any("BitElevate" in t for t in titles)


def test_rag_retriever_query():
    retriever = RAGRetriever.get_instance()
    citations = retriever.retrieve_citations("How does Cynbit build autonomous AI agents?", top_k=3)
    assert len(citations) > 0
    assert any("AI" in c.source_title or "Service" in c.source_title for c in citations)
    assert citations[0].relevance_score > 0.05
    assert len(citations[0].snippet) > 10


def test_rag_case_study_retrieval():
    retriever = RAGRetriever.get_instance()
    citations = retriever.retrieve_citations("What results did Cynbit achieve for Evento and Marketing Addict?", top_k=2)
    assert len(citations) > 0
    assert any("Case Study" in c.source_title or "Marketing Addict" in c.snippet or "Evento" in c.snippet for c in citations)
