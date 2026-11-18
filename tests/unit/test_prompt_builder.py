"""Unit tests for GroundedPromptBuilder (Phase 9 — Step 9.7)."""
from datetime import datetime, timezone
import pytest
from intelligence.correlation.alert_models import SurveillanceAlertSchema
from intelligence.rag.retrieval_engine import RetrievedEvidenceChunk
from intelligence.rag.prompt_builder import GroundedPromptBuilder


@pytest.fixture
def prompt_builder():
    return GroundedPromptBuilder()


@pytest.fixture
def sample_alert():
    return SurveillanceAlertSchema(
        alert_id="ALT_PROMPT_001",
        ticker="NSE:RELIANCE",
        company_name="Reliance Industries Limited",
        alert_timestamp=datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc),
        priority_tier="CRITICAL",
        composite_risk_score=0.88,
        confidence=0.85,
        primary_risk_driver="Pre-Announcement Timing / Leak",
        temporal_relationship="PRE_ANNOUNCEMENT_LEAK",
        sla_triage_hours=2,
        requires_human_escalation=True,
        recommended_action="Freeze audit logs and examine order book",
        market_snapshot={"return_zscore": 3.6, "volume_zscore": 4.5, "ensemble_score": 0.90},
        risk_breakdown={"market_anomaly": 0.40, "temporal_suspicion": 0.25},
    )


def test_grounded_prompt_with_evidence(prompt_builder, sample_alert):
    evidence = [
        RetrievedEvidenceChunk(
            chunk_id="chk_ril_fmcg",
            ticker="RELIANCE",
            company_name="Reliance",
            section_title="Corporate Restructuring",
            filing_date=datetime(2026, 11, 18, 4, 0, tzinfo=timezone.utc),
            content="Reliance Retail announces mega acquisition of FMCG entity for Rs 5,000 crore.",
            similarity_score=0.85,
            temporal_proximity_weight=0.90,
            hybrid_score=0.865,
            source_url="https://nseindia.com/filing/001"
        )
    ]

    payload = prompt_builder.build_investigation_prompt(sample_alert, evidence)

    assert payload.has_evidence
    assert len(payload.citation_tokens) == 1
    assert "[EVIDENCE:chk_ril_fmcg]" in payload.citation_tokens
    assert "[EVIDENCE:chk_ril_fmcg]" in payload.user_prompt
    assert "ZERO HALLUCINATION" in payload.system_prompt
    assert "3.60 sigma" in payload.user_prompt


def test_grounded_prompt_without_evidence_forces_no_evidence_clause(prompt_builder, sample_alert):
    payload = prompt_builder.build_investigation_prompt(sample_alert, [])

    assert not payload.has_evidence
    assert len(payload.citation_tokens) == 0
    assert "NO EVIDENCE FOUND" in payload.user_prompt
    assert "Insufficient evidence found" in payload.system_prompt
