"""Unit tests for InvestigationDossierGenerator (Phase 9 — Step 9.8)."""
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from intelligence.correlation.alert_models import SurveillanceAlertSchema
from intelligence.rag.vector_store import DocumentChunkVectorModel, VectorStoreRepository
from intelligence.rag.embedding_pipeline import CPUDenseEmbeddingPipeline
from intelligence.rag.retrieval_engine import HybridFilteredRetrievalEngine
from intelligence.rag.prompt_builder import GroundedPromptBuilder
from intelligence.rag.llm_provider import MockLLMProvider
from intelligence.rag.dossier_generator import InvestigationDossierGenerator


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    DocumentChunkVectorModel.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def dossier_generator(db_session):
    repo = VectorStoreRepository(session=db_session)
    embedder = CPUDenseEmbeddingPipeline(use_mock=True)
    retriever = HybridFilteredRetrievalEngine(vector_repo=repo, embedding_pipeline=embedder)
    builder = GroundedPromptBuilder()
    llm = MockLLMProvider()
    return InvestigationDossierGenerator(retriever, builder, llm), repo, embedder


def test_dossier_generation_with_grounded_evidence(dossier_generator):
    generator, repo, embedder = dossier_generator
    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)

    # Insert verified filing for RELIANCE
    text = "Reliance Retail announces mega acquisition of FMCG entity for Rs 5,000 crore."
    repo.insert_chunk(
        chunk_id="chk_ril_fmcg",
        doc_id="doc_ril",
        ticker="RELIANCE",
        company_name="Reliance Industries",
        filing_date=t0 - timedelta(hours=6),
        section_title="Corporate Restructuring",
        chunk_index=1,
        content=text,
        token_count=12,
        metadata_header="[Reliance]",
        embedding=embedder.embed_text(text).vector
    )

    alert = SurveillanceAlertSchema(
        alert_id="ALT_RAG_001",
        ticker="NSE:RELIANCE",
        company_name="Reliance Industries Limited",
        alert_timestamp=t0,
        priority_tier="HIGH",
        composite_risk_score=0.78,
        confidence=0.85,
        primary_risk_driver="Pre-Announcement Timing / Leak",
        temporal_relationship="PRE_ANNOUNCEMENT_LEAK",
        sla_triage_hours=8,
        requires_human_escalation=True,
        recommended_action="Conduct formal compliance review",
        market_snapshot={"return_zscore": 3.2, "volume_zscore": 4.1, "ensemble_score": 0.85},
        risk_breakdown={"market_anomaly": 0.35, "temporal_suspicion": 0.20},
    )

    dossier = generator.generate_dossier(alert)

    assert dossier.alert_id == "ALT_RAG_001"
    assert dossier.ticker == "NSE:RELIANCE"
    assert dossier.has_sufficient_evidence
    assert len(dossier.evidence_citations) >= 1
    assert any("chk_ril_fmcg" in c for c in dossier.evidence_citations)
    assert len(dossier.recommended_inquiries) >= 3


def test_dossier_generation_without_evidence_handles_insufficient_evidence(dossier_generator):
    generator, repo, embedder = dossier_generator
    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)

    # Alert with zero matching filings in database
    alert = SurveillanceAlertSchema(
        alert_id="ALT_NO_EVID_001",
        ticker="NSE:INFY",
        company_name="Infosys Limited",
        alert_timestamp=t0,
        priority_tier="CRITICAL",
        composite_risk_score=0.90,
        confidence=0.70,
        primary_risk_driver="Unexplained Non-Disclosure Anomaly",
        temporal_relationship="UNEXPLAINED_ABSENCE",
        sla_triage_hours=2,
        requires_human_escalation=True,
        recommended_action="Immediate forensic escalation",
        market_snapshot={"return_zscore": 4.5, "volume_zscore": 5.2, "ensemble_score": 0.92},
        risk_breakdown={"market_anomaly": 0.40, "unexplained_penalty": 0.15},
    )

    dossier = generator.generate_dossier(alert)

    assert not dossier.has_sufficient_evidence
    assert len(dossier.evidence_citations) == 0
    assert "Insufficient evidence found" in dossier.relevant_disclosures[0]
    assert "High uncertainty" in dossier.uncertainty_and_limitations
