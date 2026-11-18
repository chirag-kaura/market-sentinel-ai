"""
Grounded Prompt Engineering and Citation Injection Module.
Phase 9 — Step 9.7: Constructs zero-hallucination investigation prompts binding
market anomaly metrics, temporal relationships, retrieved evidence chunks, and mandatory citation tokens.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from intelligence.correlation.alert_models import SurveillanceAlertSchema
from intelligence.rag.retrieval_engine import RetrievedEvidenceChunk


@dataclass(frozen=True)
class GroundedPromptPayload:
    """Formatted prompt payload ready for LLM generation."""
    system_prompt: str
    user_prompt: str
    citation_tokens: List[str]
    has_evidence: bool


class GroundedPromptBuilder:
    """
    Constructs factual, evidence-grounded prompt templates for LLM investigation assistants.
    Enforces strict regulatory directives:
    1. Zero speculation: If evidence is absent, the LLM must state 'Insufficient evidence found.'
    2. Mandatory citations: Every factual statement must reference an explicit [CITATION_ID].
    3. Ethical integrity: Never generate definitive accusations of criminality.
    """

    SYSTEM_PROMPT = (
        "You are Market Sentinel AI, a specialized regulatory surveillance decision-support assistant.\n"
        "Your role is to explain statistical market anomalies and correlate them with retrieved disclosures.\n\n"
        "MANDATORY OPERATIONAL DIRECTIVES:\n"
        "1. GROUNDING & ZERO HALLUCINATION: Rely STRICTLY on the provided market metrics and retrieved evidence.\n"
        "2. ZERO FABRICATION: If no supporting evidence exists in the prompt, state explicitly: 'Insufficient evidence found.'\n"
        "3. CITATIONS: Every claim referencing corporate news, dates, or financial results MUST include its exact citation token e.g. [EVIDENCE:chunk_id].\n"
        "4. PRODUCT BOUNDARY: You are an investigative decision-support tool, NOT an automated accusation engine. Describe market behavior objectively.\n"
        "5. UNCERTAINTY: Explicitly state confidence levels, limitations, and potential alternative explanations."
    )

    def build_investigation_prompt(
        self,
        alert: SurveillanceAlertSchema,
        evidence_chunks: List[RetrievedEvidenceChunk]
    ) -> GroundedPromptPayload:
        """Builds a grounded investigation prompt for a surveillance alert."""
        lines = [
            f"### SURVEILLANCE ALERT DOSSIER: {alert.alert_id}",
            f"- Equity Symbol: {alert.ticker} ({alert.company_name})",
            f"- Alert Timestamp: {alert.alert_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"- Priority Tier: {alert.priority_tier}",
            f"- Composite Risk Score: {alert.composite_risk_score:.3f} (Confidence: {alert.confidence:.2f})",
            f"- Primary Risk Driver: {alert.primary_risk_driver}",
            f"- Temporal Relationship: {alert.temporal_relationship}",
            f"- Recommended Compliance Action: {alert.recommended_action}",
            "",
            "### QUANTITATIVE MARKET METRICS:",
            f"- Return Z-Score: {alert.market_snapshot.get('return_zscore', 0.0):.2f} sigma",
            f"- Volume Z-Score: {alert.market_snapshot.get('volume_zscore', 0.0):.2f} sigma",
            f"- Ensemble Model Anomaly Score: {alert.market_snapshot.get('ensemble_score', 0.0):.3f}",
            "",
            "### RETRIEVED CORPORATE EVIDENCE & DISCLOSURES:"
        ]

        citation_tokens: List[str] = []
        has_evidence = len(evidence_chunks) > 0

        if not has_evidence:
            lines.append("NO EVIDENCE FOUND: No contemporaneous news or regulatory filings were retrieved within the lookback window.")
        else:
            for idx, chunk in enumerate(evidence_chunks, 1):
                cite_token = f"[EVIDENCE:{chunk.chunk_id}]"
                citation_tokens.append(cite_token)
                lines.append(
                    f"{idx}. {cite_token} Section: '{chunk.section_title}' (Filing Date: {chunk.filing_date.strftime('%Y-%m-%d')} | Hybrid Score: {chunk.hybrid_score:.3f})\n"
                    f"   \"{chunk.content}\"\n"
                )

        lines.extend([
            "### REQUIRED INVESTIGATION STRUCTURE:",
            "Produce an investigation brief containing:",
            "1. Alert Executive Summary",
            "2. Observed Market Price & Volume Dynamics",
            "3. Correlation with Corporate Disclosures (with exact citations)",
            "4. Temporal Suspicion Analysis (Lead/Lag Assessment)",
            "5. Investigation Limitations & Uncertainty",
            "6. Actionable Next Steps for Compliance Desk"
        ])

        user_prompt = "\n".join(lines)

        return GroundedPromptPayload(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            citation_tokens=citation_tokens,
            has_evidence=has_evidence
        )
