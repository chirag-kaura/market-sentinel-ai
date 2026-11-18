"""
Financial Text Chunking Strategy Module.
Phase 9 — Step 9.2: Chunks financial documents while preserving semantic sentence boundaries,
section headings, company identifiers, timestamps, and metadata tags for pgvector retrieval.
"""

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Dict, List, Optional, Tuple
from intelligence.rag.document_parser import ParsedDocumentResult, ParsedSection


@dataclass(frozen=True)
class DocumentChunk:
    """A semantic chunk of a financial document ready for dense vector embedding."""
    chunk_id: str
    doc_id: str
    ticker: str
    company_name: str
    filing_date: datetime
    section_title: str
    chunk_index: int
    content: str
    token_count: int
    metadata_header: str  # Prepended context string: "[Company: X | Ticker: Y | Section: Z | Date: T]"
    source_url: Optional[str]


class FinancialTextChunker:
    """
    Sentence-aware, overlapping text chunker optimized for financial filings and news.
    Preserves numerical entities, tables, and section hierarchies.
    """

    def __init__(
        self,
        target_chunk_tokens: int = 150,
        chunk_overlap_tokens: int = 30,
        max_chunk_tokens: int = 250
    ):
        self.target_chunk_tokens = target_chunk_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.max_chunk_tokens = max_chunk_tokens
        # Regex for splitting on sentences without breaking numbers (e.g. "Rs 15.4 crore")
        self.sentence_splitter = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

    def chunk_document(self, parsed_doc: ParsedDocumentResult) -> List[DocumentChunk]:
        """
        Chunks a parsed document across its structural sections, prepending
        contextual metadata headers to optimize vector retrieval relevance.
        """
        chunks: List[DocumentChunk] = []
        meta = parsed_doc.metadata
        chunk_counter = 1

        date_str = meta.filing_date.strftime("%Y-%m-%d")

        for sec in parsed_doc.sections:
            # Build metadata header to bind context into the embedding space
            header = f"[Company: {meta.company_name} | Ticker: {meta.ticker} | Section: {sec.section_title} | Date: {date_str}]"
            
            sentences = self.sentence_splitter.split(sec.content)
            current_sentences: List[str] = []
            current_tokens = 0

            for sent in sentences:
                sent_clean = sent.strip()
                if not sent_clean:
                    continue

                sent_token_len = len(sent_clean.split())

                if current_tokens + sent_token_len > self.target_chunk_tokens and current_sentences:
                    # Flush chunk
                    chunk_text = " ".join(current_sentences)
                    chunk_id = f"{meta.doc_id}_sec{sec.section_index}_chk{chunk_counter:03d}"
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            doc_id=meta.doc_id,
                            ticker=meta.ticker,
                            company_name=meta.company_name,
                            filing_date=meta.filing_date,
                            section_title=sec.section_title,
                            chunk_index=chunk_counter,
                            content=chunk_text,
                            token_count=len(chunk_text.split()),
                            metadata_header=header,
                            source_url=meta.source_url
                        )
                    )
                    chunk_counter += 1

                    # Retain overlap sentences
                    overlap_sentences: List[str] = []
                    overlap_tokens = 0
                    for prev_s in reversed(current_sentences):
                        s_len = len(prev_s.split())
                        if overlap_tokens + s_len <= self.chunk_overlap_tokens:
                            overlap_sentences.insert(0, prev_s)
                            overlap_tokens += s_len
                        else:
                            break
                    current_sentences = overlap_sentences + [sent_clean]
                    current_tokens = sum(len(s.split()) for s in current_sentences)
                else:
                    current_sentences.append(sent_clean)
                    current_tokens += sent_token_len

            # Flush remaining sentences in section
            if current_sentences:
                chunk_text = " ".join(current_sentences)
                chunk_id = f"{meta.doc_id}_sec{sec.section_index}_chk{chunk_counter:03d}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=meta.doc_id,
                        ticker=meta.ticker,
                        company_name=meta.company_name,
                        filing_date=meta.filing_date,
                        section_title=sec.section_title,
                        chunk_index=chunk_counter,
                        content=chunk_text,
                        token_count=len(chunk_text.split()),
                        metadata_header=header,
                        source_url=meta.source_url
                    )
                )
                chunk_counter += 1

        return chunks
