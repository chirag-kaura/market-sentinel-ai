"""
Financial Disclosure Document Parsing and Normalization Module.
Phase 9 — Step 9.1: Ingests raw financial announcements, regulatory filings, and press releases,
stripping pagination noise, detecting section boundaries, and extracting structured metadata.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import html
import re
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DocumentMetadata:
    """Standardized metadata describing a parsed financial document or filing."""
    doc_id: str
    ticker: str
    company_name: str
    filing_date: datetime
    doc_type: str  # e.g., "BOARD_MEETING_OUTCOME", "FINANCIAL_RESULTS", "REGULATORY_ORDER", "PRESS_RELEASE"
    source_url: Optional[str]
    checksum: str
    total_pages: int


@dataclass(frozen=True)
class ParsedSection:
    """A distinct structural section of a parsed corporate document."""
    section_index: int
    section_title: str
    content: str
    page_number: int
    token_count: int


@dataclass(frozen=True)
class ParsedDocumentResult:
    """Complete structured output from financial document parsing."""
    metadata: DocumentMetadata
    sections: Tuple[ParsedSection, ...]
    full_cleaned_text: str
    has_financial_tables: bool


class FinancialDocumentParser:
    """
    High-throughput, CPU-efficient document parser specialized for Indian corporate filings
    (BSE/NSE exchange disclosures) and regulatory announcements (SEBI orders).
    """

    # Headers, footers, CIN markers, and pagination artifacts common in Indian filings
    PAGINATION_PATTERNS = [
        re.compile(r"^\s*page\s+\d+\s*(?:of\s+\d+)?\s*$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*[-—]\s*\d+\s*[-—]\s*$", re.MULTILINE),
        re.compile(r"\bCIN\s*:\s*[A-Z0-9]{21}\b", re.IGNORECASE),
        re.compile(r"\bRegd\.\s*Office\s*:.*?(?=\n|$)", re.IGNORECASE),
        re.compile(r"\bPhone\s*:.*?(?=\n|$)", re.IGNORECASE),
        re.compile(r"\bWebsite\s*:.*?(?=\n|$)", re.IGNORECASE),
    ]

    # Standard corporate filing section headers
    SECTION_HEADER_PATTERNS = [
        (re.compile(r"^\s*(?:item\s+\d+[:.]?\s*)?(?:outcome\s+of\s+(?:the\s+)?board\s+meeting)\b", re.IGNORECASE | re.MULTILINE), "Outcome of Board Meeting"),
        (re.compile(r"^\s*(?:item\s+\d+[:.]?\s*)?(?:financial\s+results|unaudited\s+financial\s+results|audited\s+financial\s+results)\b", re.IGNORECASE | re.MULTILINE), "Financial Results"),
        (re.compile(r"^\s*(?:item\s+\d+[:.]?\s*)?(?:management\s+discussion\s+and\s+analysis)\b", re.IGNORECASE | re.MULTILINE), "Management Discussion & Analysis"),
        (re.compile(r"^\s*(?:item\s+\d+[:.]?\s*)?(?:show\s+cause\s+notice|adjudication\s+order|regulatory\s+action)\b", re.IGNORECASE | re.MULTILINE), "Regulatory Order / Inquiry"),
        (re.compile(r"^\s*(?:item\s+\d+[:.]?\s*)?(?:dividend\s+recommendation|declaration\s+of\s+dividend)\b", re.IGNORECASE | re.MULTILINE), "Dividend Declaration"),
        (re.compile(r"^\s*(?:item\s+\d+[:.]?\s*)?(?:acquisition|merger|demerger|business\s+transfer)\b", re.IGNORECASE | re.MULTILINE), "Corporate Restructuring / M&A"),
    ]

    # Tabular markers (e.g. rows of numbers separated by tabs/pipes)
    TABLE_PATTERN = re.compile(r"(?:\||[\t\s]{2,})\s*[-+]?\d[\d,.]*\s*(?:\||[\t\s]{2,})\s*[-+]?\d[\d,.]*")

    def parse_document(
        self,
        doc_id: str,
        raw_text: str,
        ticker: str,
        company_name: str,
        filing_date: datetime,
        doc_type: str = "EXCHANGE_FILING",
        source_url: Optional[str] = None
    ) -> ParsedDocumentResult:
        """Parses raw filing text into sectioned, metadata-enriched representation."""
        if filing_date.tzinfo is None:
            filing_date = filing_date.replace(tzinfo=timezone.utc)

        # 1. Unescape HTML and normalize whitespace
        working_text = html.unescape(raw_text or "")
        working_text = re.sub(r"<[^>]+>", " ", working_text)

        # 2. Strip pagination, CIN codes, and boilerplate registered office footers
        for pattern in self.PAGINATION_PATTERNS:
            working_text = pattern.sub("", working_text)

        # Check for presence of tabular financial statements
        has_tables = bool(self.TABLE_PATTERN.search(working_text))

        # 3. Detect Sections
        lines = [line.strip() for line in working_text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)

        sections: List[ParsedSection] = []
        current_title = "Overview / General Disclosure"
        current_content_lines: List[str] = []
        section_idx = 1
        page_num = 1

        for line in lines:
            # Check for page boundary marker in synthetic multi-page inputs
            if line.startswith("--- PAGE BREAK ---"):
                page_num += 1
                continue

            matched_title = None
            for pattern, title in self.SECTION_HEADER_PATTERNS:
                if pattern.search(line):
                    matched_title = title
                    break

            if matched_title:
                # Flush existing section
                if current_content_lines:
                    sec_text = " ".join(current_content_lines)
                    sections.append(
                        ParsedSection(
                            section_index=section_idx,
                            section_title=current_title,
                            content=sec_text,
                            page_number=page_num,
                            token_count=len(sec_text.split())
                        )
                    )
                    section_idx += 1
                    current_content_lines = []
                current_title = matched_title
                current_content_lines.append(line)
            else:
                current_content_lines.append(line)

        # Flush final section
        if current_content_lines:
            sec_text = " ".join(current_content_lines)
            sections.append(
                ParsedSection(
                    section_index=section_idx,
                    section_title=current_title,
                    content=sec_text,
                    page_number=page_num,
                    token_count=len(sec_text.split())
                )
            )

        # Compute checksum
        checksum = hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()

        metadata = DocumentMetadata(
            doc_id=doc_id,
            ticker=ticker,
            company_name=company_name,
            filing_date=filing_date,
            doc_type=doc_type,
            source_url=source_url,
            checksum=checksum,
            total_pages=max(1, page_num)
        )

        return ParsedDocumentResult(
            metadata=metadata,
            sections=tuple(sections),
            full_cleaned_text=cleaned_text,
            has_financial_tables=has_tables
        )
