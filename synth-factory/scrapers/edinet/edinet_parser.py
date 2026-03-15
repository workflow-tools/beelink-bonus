"""
EDINET document parser — extract structured segments from downloaded filings.

Securities reports (有価証券報告書) follow a standardized structure mandated by
the FSA. This parser extracts the key sections into named segments that map
directly to synth-factory document_type segment definitions.

Standard 有価証券報告書 sections:
  Part 1: 企業情報 (Company Information)
    1. 企業の概況 (Company Overview)
       - 主要な経営指標等の推移 (Key Financial Indicators)
       - 沿革 (History)
       - 事業の内容 (Business Description)
       - 関係会社の状況 (Affiliated Companies)
       - 従業員の状況 (Employee Information)
    2. 事業の状況 (Business Status)
       - 経営方針 (Management Policy)
       - 事業等のリスク (Business Risks)
       - 経営者による分析 (MD&A)
       - 研究開発活動 (R&D Activities)
    3. 設備の状況 (Facilities)
    4. 提出会社の状況 (Company Status)
       - 株式等の状況 (Stock Information)
       - 役員の状況 (Directors/Officers)
       - コーポレートガバナンス (Corporate Governance)
    5. 経理の状況 (Financial Statements)
       - 連結財務諸表 (Consolidated)
       - 財務諸表 (Non-consolidated)
  Part 2: 提出会社の保証会社等の情報 (Guarantor Information)

Input: extracted ZIP contents (dict of {filename: bytes})
Output: dict of {segment_name: extracted_text}
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Segment Definitions ───────────────────────────────────────


# These map to synth-factory segment names
SECURITIES_REPORT_SEGMENTS = [
    ("company_overview", "企業の概況", [
        "主要な経営指標", "沿革", "事業の内容", "関係会社", "従業員",
    ]),
    ("business_status", "事業の状況", [
        "経営方針", "事業等のリスク", "経営者による", "MD&A", "研究開発",
    ]),
    ("md_and_a", "経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析", []),
    ("business_risks", "事業等のリスク", []),
    ("facilities", "設備の状況", []),
    ("corporate_governance", "コーポレート・ガバナンスの状況", []),
    ("stock_info", "株式等の状況", []),
    ("directors", "役員の状況", []),
    ("financial_statements", "経理の状況", [
        "連結財務諸表", "財務諸表", "注記",
    ]),
    ("accounting_policy", "重要な会計方針", []),
    ("notes", "注記事項", []),
    ("guarantor_info", "提出会社の保証会社等の情報", []),
]


# ─── Parser ─────────────────────────────────────────────────────


class EdinetParser:
    """
    Parse EDINET securities report files into structured text segments.

    Handles two primary formats:
    1. Inline XBRL (iXBRL) — HTML with embedded XBRL tags
    2. XBRL — pure XML (financial data only)

    For synth-factory purposes, we primarily want the narrative text
    (MD&A, business risks, governance) rather than the numerical XBRL data.
    """

    def parse_zip_contents(
        self,
        files: dict[str, bytes],
        doc_id: str = "",
    ) -> ParsedDocument:
        """
        Parse extracted ZIP contents into a structured document.

        Args:
            files: {filename: content_bytes} from ZIP extraction.
            doc_id: Document ID for logging.

        Returns:
            ParsedDocument with extracted segments and metadata.
        """
        result = ParsedDocument(doc_id=doc_id)

        # Identify file types
        html_files = {k: v for k, v in files.items() if k.endswith((".htm", ".html"))}
        xbrl_files = {k: v for k, v in files.items() if k.endswith(".xbrl")}
        manifest_files = {k: v for k, v in files.items() if k.endswith("manifest.xml")}

        # Prioritize inline XBRL (HTML) for narrative extraction
        # These are typically in XBRL/PublicDoc/ directory
        public_htmls = {
            k: v for k, v in html_files.items()
            if "PublicDoc" in k or "publicdoc" in k.lower()
        }

        if public_htmls:
            result = self._parse_html_files(public_htmls, result)
        elif html_files:
            result = self._parse_html_files(html_files, result)
        elif xbrl_files:
            result = self._parse_xbrl_files(xbrl_files, result)
        else:
            logger.warning(f"No parseable files found in {doc_id}")
            result.error = "No HTML or XBRL files found in ZIP"

        # Record file inventory
        result.file_inventory = {
            name: len(content) for name, content in files.items()
        }
        result.total_files = len(files)
        result.total_bytes = sum(len(v) for v in files.values())

        return result

    def _parse_html_files(
        self,
        html_files: dict[str, bytes],
        result: ParsedDocument,
    ) -> ParsedDocument:
        """
        Extract text segments from inline XBRL / HTML files.

        Securities reports typically have one or more HTML files, each
        containing sections of the report. We parse all of them and
        attempt to identify sections by heading patterns.
        """
        all_text = ""
        for filename in sorted(html_files.keys()):
            try:
                content = html_files[filename]
                text = self._html_to_text(content)
                if text:
                    all_text += f"\n\n{'='*40}\n[{filename}]\n{'='*40}\n\n{text}"
            except Exception as e:
                logger.warning(f"Failed to parse HTML file {filename}: {e}")
                continue

        if not all_text:
            result.error = "No text extracted from HTML files"
            return result

        result.full_text = all_text
        result.content_format = "html"

        # Extract segments by matching section headings
        result.segments = self._extract_segments(all_text)

        if result.segments:
            result.parsed = True

        return result

    def _parse_xbrl_files(
        self,
        xbrl_files: dict[str, bytes],
        result: ParsedDocument,
    ) -> ParsedDocument:
        """
        Extract text from XBRL files (fallback for non-inline reports).

        XBRL files contain structured financial data in XML. We extract
        the textBlock elements which contain narrative disclosures.
        """
        all_text = ""
        for filename in sorted(xbrl_files.keys()):
            try:
                content = xbrl_files[filename].decode("utf-8", errors="replace")
                # Extract textBlock elements (narrative content in XBRL)
                text_blocks = re.findall(
                    r'<[^>]*textBlock[^>]*>(.*?)</[^>]*textBlock[^>]*>',
                    content,
                    re.DOTALL | re.IGNORECASE,
                )
                for block in text_blocks:
                    cleaned = self._clean_html_tags(block)
                    if cleaned.strip():
                        all_text += cleaned + "\n\n"
            except Exception as e:
                logger.warning(f"Failed to parse XBRL file {filename}: {e}")
                continue

        if all_text:
            result.full_text = all_text
            result.content_format = "xbrl"
            result.segments = self._extract_segments(all_text)
            if result.segments:
                result.parsed = True

        return result

    def _html_to_text(self, html_bytes: bytes) -> str:
        """
        Convert HTML/iXBRL to plain text.

        Uses a lightweight regex-based approach to avoid heavy dependencies.
        For production, could be upgraded to use beautifulsoup4.
        """
        # Decode
        for encoding in ("utf-8", "shift_jis", "euc-jp", "cp932"):
            try:
                html = html_bytes.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            html = html_bytes.decode("utf-8", errors="replace")

        return self._clean_html_tags(html)

    @staticmethod
    def _clean_html_tags(html: str) -> str:
        """Strip HTML/XML tags and normalize whitespace."""
        # Remove script and style blocks
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Convert <br>, <p>, <div>, <tr> to newlines
        text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</(?:p|div|tr|li|h[1-6])>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<(?:p|div|tr|li|h[1-6])[^>]*>', '\n', text, flags=re.IGNORECASE)

        # Convert table cells to tab separation
        text = re.sub(r'</(?:td|th)>', '\t', text, flags=re.IGNORECASE)

        # Remove remaining tags
        text = re.sub(r'<[^>]+>', '', text)

        # Decode common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#12288;', '　')  # full-width space

        # Normalize whitespace (preserve Japanese full-width spaces)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _extract_segments(self, text: str) -> dict[str, str]:
        """
        Extract named segments from full document text by matching
        section heading patterns.

        Returns {segment_name: text_content} for each matched section.
        """
        segments: dict[str, str] = {}

        for seg_name, heading_pattern, sub_patterns in SECURITIES_REPORT_SEGMENTS:
            # Try to find this section in the text
            content = self._find_section(text, heading_pattern)
            if content and len(content.strip()) > 50:
                segments[seg_name] = content.strip()

        return segments

    @staticmethod
    def _find_section(text: str, heading: str) -> str:
        """
        Find a section by its heading and extract content until the next
        major heading.

        Uses a fuzzy match approach — the heading text may have extra
        whitespace, numbering, or slight variations in the actual document.
        """
        # Build a flexible pattern for the heading
        # Allow digits/punctuation before the heading text
        escaped = re.escape(heading)
        # Allow flexible whitespace within the heading
        pattern = r'[\d\.\s【】]*' + escaped.replace(r'\ ', r'\s*')

        match = re.search(pattern, text)
        if not match:
            return ""

        start = match.end()

        # Find end: next major section heading (number + heading pattern)
        # Look for patterns like "第N", "【", or numbered headings
        next_heading = re.search(
            r'\n\s*(?:第[一二三四五六七八九十百\d]+|【|[０-９\d]+\s*[\.\．])',
            text[start:],
        )

        if next_heading:
            end = start + next_heading.start()
        else:
            # Take up to 10000 chars if no next heading found
            end = min(start + 10000, len(text))

        return text[start:end]


# ─── Result Model ───────────────────────────────────────────────


@dataclass
class ParsedDocument:
    """Result of parsing an EDINET filing."""
    doc_id: str = ""
    content_format: str = ""           # "html" or "xbrl"
    full_text: str = ""                # Complete extracted text
    segments: dict[str, str] = field(default_factory=dict)
    file_inventory: dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    total_bytes: int = 0
    parsed: bool = False
    error: str = ""

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def total_text_length(self) -> int:
        return len(self.full_text)

    def summary(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "format": self.content_format,
            "text_length": self.total_text_length,
            "segments": list(self.segments.keys()),
            "segment_count": self.segment_count,
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "parsed": self.parsed,
            "error": self.error,
        }
