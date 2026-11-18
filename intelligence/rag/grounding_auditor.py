"""
Hallucination and Zero-Evidence Grounding Evaluation Harness.
Phase 9 — Step 9.9: Audits generated dossiers for unsupported claims, citation fidelity,
empty-evidence adherence, and cross-company entity contamination.
"""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple
from intelligence.rag.dossier_generator import StructuredInvestigationDossier
from intelligence.rag.retrieval_engine import RetrievedEvidenceChunk


@dataclass(frozen=True)
class GroundingAuditReport:
    """Detailed report auditing dossier grounding integrity and hallucination risk."""
    is_grounded: bool
    citation_precision: float          # Ratio of valid cited chunk IDs to total citations
    unsupported_claims_count: int      # Citations referencing non-existent chunks
    zero_evidence_adherence: bool      # True if zero-evidence alerts explicitly declare insufficient evidence
    cross_company_contamination: bool  # True if entities belonging to other tickers appear in citations
    faithfulness_score: float          # Composite metric in [0.0, 1.0]


class HallucinationGroundingAuditor:
    """
    Automated evaluation harness verifying that LLM-generated surveillance dossiers
    strictly reflect retrieved ground-truth evidence without hallucinating facts or citations.
    """

    CITATION_REGEX = re.compile(r"\[EVIDENCE:([a-zA-Z0-9_\-]+)\]")

    def audit_dossier(
        self,
        dossier: StructuredInvestigationDossier,
        available_evidence: List[RetrievedEvidenceChunk]
    ) -> GroundingAuditReport:
        """Audits a generated dossier against the actual ground-truth evidence provided."""
        valid_chunk_ids = {c.chunk_id for c in available_evidence}

        # 1. Zero-Evidence Compliance Check
        if not available_evidence or not dossier.has_sufficient_evidence:
            has_insufficient_phrase = any(
                "insufficient evidence" in d.lower() or "no contemporaneous" in d.lower()
                for d in dossier.relevant_disclosures
            )
            # If evidence was empty, dossier must declare insufficient evidence and have 0 citations
            zero_evidence_pass = has_insufficient_phrase and (len(dossier.evidence_citations) == 0)
            return GroundingAuditReport(
                is_grounded=zero_evidence_pass,
                citation_precision=1.0 if zero_evidence_pass else 0.0,
                unsupported_claims_count=0 if zero_evidence_pass else len(dossier.evidence_citations),
                zero_evidence_adherence=zero_evidence_pass,
                cross_company_contamination=False,
                faithfulness_score=1.0 if zero_evidence_pass else 0.0
            )

        # 2. Extract and Validate Citations
        cited_ids = set()
        for cite_str in dossier.evidence_citations:
            match = self.CITATION_REGEX.search(cite_str)
            if match:
                cited_ids.add(match.group(1))

        if not cited_ids:
            # If evidence existed but no citations were made, grounding fails
            return GroundingAuditReport(
                is_grounded=False,
                citation_precision=0.0,
                unsupported_claims_count=1,
                zero_evidence_adherence=True,
                cross_company_contamination=False,
                faithfulness_score=0.0
            )

        # 3. Check for Fabricated Citations
        unsupported_citations = cited_ids.difference(valid_chunk_ids)
        unsupported_count = len(unsupported_citations)
        precision = (len(cited_ids) - unsupported_count) / len(cited_ids)

        # 4. Check for Cross-Company Contamination
        # Citations must all belong to chunks whose ticker matches the dossier ticker
        clean_dossier_ticker = dossier.ticker.replace("NSE:", "").replace("BSE:", "")
        cross_contamination = any(
            c.ticker != clean_dossier_ticker
            for c in available_evidence
            if c.chunk_id in cited_ids
        )

        is_grounded = (unsupported_count == 0) and not cross_contamination and (precision >= 0.95)
        faithfulness = round(precision * (0.0 if cross_contamination else 1.0), 3)

        return GroundingAuditReport(
            is_grounded=is_grounded,
            citation_precision=round(precision, 3),
            unsupported_claims_count=unsupported_count,
            zero_evidence_adherence=True,
            cross_company_contamination=cross_contamination,
            faithfulness_score=faithfulness
        )
