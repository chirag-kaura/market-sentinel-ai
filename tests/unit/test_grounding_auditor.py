"""Unit tests for HallucinationGroundingAuditor (Phase 9 — Step 9.9)."""
from datetime import datetime, timezone
import pytest
from intelligence.rag.dossier_generator import StructuredInvestigationDossier
from intelligence.rag.retrieval_engine import RetrievedEvidenceChunk
from intelligence.rag.grounding_auditor import HallucinationGroundingAuditor


@pytest.fixture
def auditor():
    return HallucinationGroundingAuditor()


def test_perfectly_grounded_dossier_audit(auditor):
    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    evidence = [
        RetrievedEvidenceChunk(
            chunk_id="chk_real_001",
            ticker="RELIANCE",
            company_name="Reliance Industries",
            section_title="M&A",
            filing_date=t0,
            content="Reliance acquires entity.",
            similarity_score=0.88,
            temporal_proximity_weight=0.95,
            hybrid_score=0.90,
            source_url="https://nse.com/1"
        )
    ]

    dossier = StructuredInvestigationDossier(
        alert_id="ALT_001",
        ticker="NSE:RELIANCE",
        company_name="Reliance Industries",
        alert_summary="Alert summary",
        observed_market_behavior="Price moved 3 sigma",
        supporting_signals=[],
        relevant_disclosures=["Filing regarding M&A [EVIDENCE:chk_real_001]"],
        contextual_relationship="Coincident",
        evidence_citations=["[EVIDENCE:chk_real_001]"],
        uncertainty_and_limitations="None",
        recommended_inquiries=[],
        has_sufficient_evidence=True,
        model_version="mock"
    )

    report = auditor.audit_dossier(dossier, evidence)

    assert report.is_grounded
    assert report.citation_precision == 1.0
    assert report.unsupported_claims_count == 0
    assert not report.cross_company_contamination
    assert report.faithfulness_score == 1.0


def test_hallucinated_citation_detection(auditor):
    t0 = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
    evidence = [
        RetrievedEvidenceChunk(
            chunk_id="chk_real_001",
            ticker="TATAMOTORS",
            company_name="Tata Motors",
            section_title="Q3",
            filing_date=t0,
            content="Tata Motors earnings.",
            similarity_score=0.80,
            temporal_proximity_weight=0.90,
            hybrid_score=0.83,
            source_url=None
        )
    ]

    # Dossier hallucinates citation to 'chk_invented_999'
    dossier = StructuredInvestigationDossier(
        alert_id="ALT_002",
        ticker="NSE:TATAMOTORS",
        company_name="Tata Motors",
        alert_summary="Alert",
        observed_market_behavior="Volume spike",
        supporting_signals=[],
        relevant_disclosures=["Disclosure [EVIDENCE:chk_invented_999]"],
        contextual_relationship="Suspect",
        evidence_citations=["[EVIDENCE:chk_invented_999]"],
        uncertainty_and_limitations="High",
        recommended_inquiries=[],
        has_sufficient_evidence=True,
        model_version="mock"
    )

    report = auditor.audit_dossier(dossier, evidence)

    assert not report.is_grounded
    assert report.unsupported_claims_count == 1
    assert report.citation_precision == 0.0


def test_zero_evidence_adherence_pass(auditor):
    # Empty evidence must result in zero-evidence adherence pass
    dossier = StructuredInvestigationDossier(
        alert_id="ALT_003",
        ticker="NSE:INFY",
        company_name="Infosys",
        alert_summary="Alert",
        observed_market_behavior="Price shock",
        supporting_signals=[],
        relevant_disclosures=["Insufficient evidence found. No contemporaneous filings matched."],
        contextual_relationship="Unexplained",
        evidence_citations=[],
        uncertainty_and_limitations="High uncertainty",
        recommended_inquiries=[],
        has_sufficient_evidence=False,
        model_version="mock"
    )

    report = auditor.audit_dossier(dossier, [])

    assert report.is_grounded
    assert report.zero_evidence_adherence
    assert report.unsupported_claims_count == 0
