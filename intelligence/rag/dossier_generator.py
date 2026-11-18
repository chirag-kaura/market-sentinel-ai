"""
Structured Investigation Dossier Generation Engine.
Phase 9 — Step 9.8: Orchestrates hybrid retrieval, prompt injection, and LLM inference
to generate standardized, 8-point regulatory surveillance investigation dossiers.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from intelligence.correlation.alert_models import SurveillanceAlertSchema
from intelligence.rag.retrieval_engine import HybridFilteredRetrievalEngine, RetrievedEvidenceChunk
from intelligence.rag.prompt_builder import GroundedPromptBuilder
from intelligence.rag.llm_provider import BaseLLMProvider, LLMGenerationResponse


@dataclass(frozen=True)
class StructuredInvestigationDossier:
    """Standardized 8-point regulatory surveillance dossier."""
    alert_id: str
    ticker: str
    company_name: str
    alert_summary: str
    observed_market_behavior: str
    supporting_signals: List[str]
    relevant_disclosures: List[str]
    contextual_relationship: str
    evidence_citations: List[str]
    uncertainty_and_limitations: str
    recommended_inquiries: List[str]
    has_sufficient_evidence: bool
    model_version: str


class InvestigationDossierGenerator:
    """
    Orchestrates the complete RAG investigation pipeline to produce auditable,
    citation-backed surveillance dossiers for human compliance officers.
    """

    def __init__(
        self,
        retrieval_engine: HybridFilteredRetrievalEngine,
        prompt_builder: GroundedPromptBuilder,
        llm_provider: BaseLLMProvider
    ):
        self.retriever = retrieval_engine
        self.prompt_builder = prompt_builder
        self.llm = llm_provider

    def generate_dossier(
        self,
        alert: SurveillanceAlertSchema,
        search_query: Optional[str] = None,
        lookback_days: float = 14.0
    ) -> StructuredInvestigationDossier:
        """Generates a complete investigation dossier for an incoming surveillance alert."""
        query = search_query or f"{alert.company_name} {alert.primary_risk_driver} quarterly results earnings announcement"
        clean_ticker = alert.ticker.replace("NSE:", "").replace("BSE:", "")

        # 1. Retrieve grounded evidence chunks
        evidence_chunks = self.retriever.retrieve_evidence(
            query=query,
            ticker=clean_ticker,
            anchor_timestamp=alert.alert_timestamp,
            lookback_days=lookback_days,
            top_k=3
        )

        # 2. Build grounded prompt payload
        prompt_payload = self.prompt_builder.build_investigation_prompt(alert, evidence_chunks)

        # 3. Invoke LLM provider
        llm_response = self.llm.generate(
            prompt=prompt_payload.user_prompt,
            system_prompt=prompt_payload.system_prompt,
            temperature=0.1
        )

        # 4. Synthesize structured 8-point dossier
        return self._synthesize_dossier(alert, evidence_chunks, llm_response, prompt_payload.has_evidence)

    def _synthesize_dossier(
        self,
        alert: SurveillanceAlertSchema,
        evidence: List[RetrievedEvidenceChunk],
        llm_res: LLMGenerationResponse,
        has_evidence: bool
    ) -> StructuredInvestigationDossier:
        """Extracts and standardizes the 8 mandatory surveillance points."""
        ret_z = alert.market_snapshot.get("return_zscore", 0.0)
        vol_z = alert.market_snapshot.get("volume_zscore", 0.0)

        market_behavior = (
            f"Observed return deviation of {ret_z:.2f} sigma and trading volume deviation of {vol_z:.2f} sigma "
            f"relative to the 20-day trailing baseline on {alert.alert_timestamp.strftime('%Y-%m-%d')}."
        )

        supporting_signals = [
            f"Multi-model ensemble anomaly score: {alert.market_snapshot.get('ensemble_score', 0.0):.3f}",
            f"Temporal alignment classification: {alert.temporal_relationship}",
            f"Composite risk score: {alert.composite_risk_score:.3f} [{alert.priority_tier}]"
        ]

        if has_evidence:
            citations = [f"[EVIDENCE:{c.chunk_id}]" for c in evidence]
            disclosures = [
                f"{c.company_name} disclosure regarding '{c.section_title}' filed on {c.filing_date.strftime('%Y-%m-%d')} [EVIDENCE:{c.chunk_id}]: {c.content[:120]}..."
                for c in evidence
            ]
            contextual_rel = f"Temporal relationship identified as {alert.temporal_relationship}. Evidence cited from {len(evidence)} verified filing sections."
            uncertainty = "Findings are grounded in public corporate filings. Private bilateral block trades or non-disclosed negotiations remain unverifiable without regulatory order book queries."
            has_sufficient = True
        else:
            citations = []
            disclosures = ["Insufficient evidence found. No contemporaneous public filings matched within lookback window."]
            contextual_rel = "Unexplained market anomaly. No corresponding news or regulatory filings were detected."
            uncertainty = "High uncertainty: statistical movement is confirmed by price-volume data, but narrative causality cannot be established."
            has_sufficient = False

        recommended_inquiries = [
            alert.recommended_action,
            "Request detailed counterparty clearing data for top 5 active broker-dealers during the anomalous trading window.",
            "Cross-reference trading ledger timestamps against internal corporate insider trading pre-clearance logs."
        ]

        summary = (
            f"Surveillance alert for {alert.ticker} classified as {alert.priority_tier} (Risk: {alert.composite_risk_score:.2f}). "
            f"Primary risk driver: {alert.primary_risk_driver}."
        )

        return StructuredInvestigationDossier(
            alert_id=alert.alert_id,
            ticker=alert.ticker,
            company_name=alert.company_name,
            alert_summary=summary,
            observed_market_behavior=market_behavior,
            supporting_signals=supporting_signals,
            relevant_disclosures=disclosures,
            contextual_relationship=contextual_rel,
            evidence_citations=citations,
            uncertainty_and_limitations=uncertainty,
            recommended_inquiries=recommended_inquiries,
            has_sufficient_evidence=has_sufficient,
            model_version=llm_res.model_name
        )
