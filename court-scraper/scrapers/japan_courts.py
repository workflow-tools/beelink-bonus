#!/usr/bin/env python3
"""
Japan Court Case Scraper — 裁判例検索 (courts.go.jp)

Scrapes real estate and housing dispute decisions from the Supreme Court
of Japan's public case law database to extract:
- Document structure patterns (how real housing forms are referenced)
- Flaw taxonomies (what errors courts identify in contracts/forms)
- Domain-specific vocabulary and phrasing

Target: 不動産・賃貸借・住宅管理 related cases

Legal basis: Court decisions are public records in Japan.
The 裁判例検索 system is freely accessible for research purposes.

Usage:
    python japan_courts.py --search "敷金返還" --max-results 50
    python japan_courts.py --search "建物明渡" --court district --max-results 100
    python japan_courts.py --search "賃貸借契約" --date-from 2020-01-01
    python japan_courts.py --bulk  # Run all predefined real estate queries
    python japan_courts.py --resume  # Resume interrupted bulk scrape

Rate limiting: 3-5 second delays between requests (be respectful).
"""

from __future__ import annotations
import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

import httpx
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Config ────────────────────────────────────────────────────────

BASE_URL = "https://www.courts.go.jp"
# Discovered 2026-03-13: Site uses GET with query params, NOT POST
# URL pattern: /hanrei/search1/index.html?query1=...&filter[...]
SEARCH_URL = f"{BASE_URL}/hanrei/search1/index.html"
# Detail pages: /hanrei/detail/index.html?id=XXXXXX
DETAIL_BASE = f"{BASE_URL}/hanrei/detail/index.html"
# Legacy endpoints (may redirect):
LEGACY_SEARCH = f"{BASE_URL}/app/hanrei_jp/search1"
LEGACY_DETAIL = f"{BASE_URL}/app/hanrei_jp/detail"

# Respectful rate limiting
REQUEST_DELAY = 4.0  # seconds between requests
TIMEOUT = 30.0

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "japan"

# Real estate related search queries with categories
REAL_ESTATE_QUERIES = [
    # Housing management and applications
    {"keyword": "住宅管理", "category": "housing_management"},
    {"keyword": "管理組合", "category": "management_association"},
    {"keyword": "公営住宅", "category": "public_housing"},
    # Lease agreements and disputes
    {"keyword": "賃貸借契約", "category": "lease_agreement"},
    {"keyword": "建物賃貸借", "category": "building_lease"},
    {"keyword": "借地借家", "category": "land_building_lease"},
    # Security deposits
    {"keyword": "敷金返還", "category": "security_deposit"},
    {"keyword": "敷金", "category": "security_deposit"},
    # Eviction
    {"keyword": "建物明渡", "category": "eviction"},
    {"keyword": "明渡請求", "category": "eviction_claim"},
    # Rent disputes
    {"keyword": "賃料増減額", "category": "rent_adjustment"},
    {"keyword": "賃料減額", "category": "rent_reduction"},
    # Real estate transactions
    {"keyword": "不動産売買", "category": "real_estate_sale"},
    {"keyword": "重要事項説明", "category": "important_matters"},
    # Defects and warranties
    {"keyword": "瑕疵担保 建物", "category": "building_defect"},
    {"keyword": "建物瑕疵", "category": "building_defect"},
    # Guarantor contracts
    {"keyword": "連帯保証 賃貸", "category": "guarantor_lease"},
    {"keyword": "保証契約 不動産", "category": "guarantor_real_estate"},
    # Insurance related
    {"keyword": "火災保険 賃貸", "category": "fire_insurance_rental"},
    # Building contracts
    {"keyword": "建築請負契約", "category": "construction_contract"},
    {"keyword": "建物工事", "category": "building_construction"},
]


# ─── Data Models ──────────────────────────────────────────────────

@dataclass
class CaseMetadata:
    """Metadata for a single court case."""
    case_id: str = ""
    case_number: str = ""          # 事件番号
    court: str = ""                # 裁判所
    decision_date: str = ""        # 判決日
    case_title: str = ""           # 事件名
    case_type: str = ""            # 裁判区分
    url: str = ""                  # Detail page URL
    search_query: str = ""         # Query that found this
    category: str = ""             # Our category tag

@dataclass
class CaseDetail:
    """Full detail of a court case including decision text."""
    metadata: CaseMetadata
    full_text: str = ""            # 全文
    judgment: str = ""             # 主文 (judgment/ruling)
    reasoning: str = ""            # 理由 (reasoning)
    facts: str = ""                # 事実 (facts)
    referenced_statutes: list = field(default_factory=list)  # 参照条文
    # Extracted document references (contracts, forms mentioned in decision)
    document_references: list = field(default_factory=list)
    # Identified flaws/errors mentioned in the case
    identified_flaws: list = field(default_factory=list)
    scraped_at: str = ""


# ─── Scraper ──────────────────────────────────────────────────────

class JapanCourtScraper:
    """
    Scraper for the Japanese court case database (裁判例検索).

    Approach:
    1. Submit POST search with keywords
    2. Parse result list HTML for case links
    3. Follow each link to get full decision text
    4. Extract structured sections (主文, 理由, 事実)
    5. Identify document references and flaw patterns
    """

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            timeout=TIMEOUT,
            headers={
                "User-Agent": "VilseckKI-Research-Bot/1.0 (academic research; "
                              "contact: workflow.tools@icloud.com)",
                "Accept-Language": "ja,en;q=0.5",
            },
            follow_redirects=True,
        )
        self.progress_file = output_dir / ".progress.jsonl"
        self.scraped_ids: set[str] = set()
        self._load_progress()

    def _load_progress(self):
        """Load previously scraped case IDs for resume support."""
        if self.progress_file.exists():
            with open(self.progress_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.scraped_ids.add(data.get("case_id", ""))
                        except json.JSONDecodeError:
                            continue
            logger.info(f"Loaded {len(self.scraped_ids)} previously scraped cases")

    def search(
        self,
        keyword: str,
        court_type: str = "",
        date_from: str = "",
        date_to: str = "",
        max_results: int = 50,
    ) -> list[CaseMetadata]:
        """
        Search for cases matching the keyword.

        Discovered 2026-03-13: The site uses GET requests with query params:
          /hanrei/search1/index.html?query1=敷金返還+賃貸借&filter[courtType]=...
        The 統合検索 (unified search) returns up to 2000 results per query.
        Court-specific tabs (最高裁判所, 高等裁判所, 下級裁判所) narrow results.

        Args:
            keyword: Japanese search term (e.g., "敷金返還")
            court_type: Filter by court ("supreme", "high", "district", "summary")
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            max_results: Maximum results to retrieve

        Returns:
            List of CaseMetadata objects
        """
        logger.info(f"Searching: '{keyword}' (max {max_results} results)")

        # Build GET parameters matching the actual site's URL structure
        # (mapped from live site exploration on 2026-03-13)
        params = {
            "query1": keyword,
            "query2": "",  # Additional required keywords (AND)
        }

        # Date filters use Japanese era calendar
        # Format: filter[judgeGengoFrom], filter[judgeYearFrom], etc.
        if date_from:
            era, year, month, day = self._to_japanese_era(date_from)
            if era:
                params["filter[judgeGengoFrom]"] = era
                params["filter[judgeYearFrom]"] = str(year)
                params["filter[judgeMonthFrom]"] = str(month)
                params["filter[judgeDayFrom]"] = str(day)
        if date_to:
            era, year, month, day = self._to_japanese_era(date_to)
            if era:
                params["filter[judgeGengoTo]"] = era
                params["filter[judgeYearTo]"] = str(year)
                params["filter[judgeMonthTo]"] = str(month)
                params["filter[judgeDayTo]"] = str(day)

        # Court type filtering
        if court_type:
            params["filter[courtType]"] = court_type

        # Case number fields (leave empty for broad search)
        for key in ["jikenGengo", "jikenYear", "jikenCode", "jikenNumber",
                     "courtSection", "courtName", "branchName"]:
            params[f"filter[{key}]"] = ""

        cases = []
        page = 1

        while len(cases) < max_results:
            try:
                page_params = dict(params)
                if page > 1:
                    page_params["page"] = str(page)

                response = self.client.get(SEARCH_URL, params=page_params)

                # Handle redirect (site may redirect /app/hanrei_jp/ to /hanrei/)
                if response.status_code in (301, 302, 303, 307, 308):
                    redirect_url = response.headers.get("location", "")
                    logger.info(f"Redirected to: {redirect_url}")
                    response = self.client.get(redirect_url)

                response.raise_for_status()

                page_cases = self._parse_search_results(response.text, keyword)

                if not page_cases:
                    logger.info(f"No more results on page {page}")
                    break

                cases.extend(page_cases)
                logger.info(f"Page {page}: found {len(page_cases)} cases (total: {len(cases)})")

                page += 1
                time.sleep(REQUEST_DELAY)

            except httpx.HTTPError as e:
                logger.error(f"Search request failed: {e}")
                break

        return cases[:max_results]

    @staticmethod
    def _to_japanese_era(date_str: str) -> tuple:
        """
        Convert YYYY-MM-DD to Japanese era components.

        Returns (era_name, era_year, month, day) or (None,...) if invalid.
        Japanese eras:
          令和 (Reiwa): 2019-05-01 onwards
          平成 (Heisei): 1989-01-08 to 2019-04-30
          昭和 (Showa): 1926-12-25 to 1989-01-07
        """
        try:
            parts = date_str.split("-")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            return (None, 0, 0, 0)

        if year >= 2019:
            return ("令和", year - 2018, month, day)
        elif year >= 1989:
            return ("平成", year - 1988, month, day)
        elif year >= 1926:
            return ("昭和", year - 1925, month, day)
        return (None, 0, 0, 0)

    def _parse_search_results(self, html: str, query: str) -> list[CaseMetadata]:
        """
        Parse search results HTML to extract case metadata.

        Discovered 2026-03-13 via Chrome exploration:
        - Detail page URL pattern: /hanrei/{id}/detail2/index.html
        - PDF full text URL: /assets/hanrei/hanrei-pdf-{id}.pdf
        - Results are in table rows or list items
        - The search results page links use href patterns like:
          /hanrei/XXXXX/detail2/index.html or ?id=XXXXX
        """
        soup = BeautifulSoup(html, "html.parser")
        cases = []

        # Try multiple selectors since the exact HTML structure may vary
        result_items = (
            soup.select("table.searchResult tr")
            or soup.select("div.result-list li")
            or soup.select(".hanrei-list tr")
            or soup.select("table tr")
        )

        # Also look for links matching the confirmed URL pattern
        if not result_items:
            # Fallback: find all links to detail pages
            detail_links = soup.find_all("a", href=re.compile(
                r"/hanrei/\d+/detail|detail.*index\.html|[?&]id=\d+"
            ))
            for link in detail_links:
                parent = link.find_parent(["tr", "li", "div"])
                if parent and parent not in result_items:
                    result_items.append(parent)

        for item in result_items:
            try:
                # Look for links to detail pages — multiple URL patterns
                link = item.find("a", href=re.compile(
                    r"/hanrei/\d+/detail|detail.*index|[?&]id=\d+"
                ))
                if not link:
                    # Fallback: any link with "hanrei" in it
                    link = item.find("a", href=re.compile(r"hanrei"))
                if not link:
                    continue

                href = link.get("href", "")
                if not href:
                    continue

                # Build full URL
                if href.startswith("/"):
                    url = BASE_URL + href
                elif not href.startswith("http"):
                    url = BASE_URL + "/" + href
                else:
                    url = href

                # Extract case ID from URL
                # Pattern 1: /hanrei/{id}/detail2/index.html (confirmed)
                case_id_match = re.search(r"/hanrei/(\d+)/detail", href)
                if not case_id_match:
                    # Pattern 2: ?id=XXXXX
                    case_id_match = re.search(r"[?&]id=(\d+)", href)
                if not case_id_match:
                    # Pattern 3: detail followed by number
                    case_id_match = re.search(r"detail(\d+)", href)
                case_id = case_id_match.group(1) if case_id_match else href

                # Extract text fields from the row/item
                cells = item.find_all(["td", "span", "div"])
                text_parts = [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]

                metadata = CaseMetadata(
                    case_id=case_id,
                    url=url,
                    search_query=query,
                )

                # Try to extract structured fields from cells
                for text in text_parts:
                    # Date pattern: 令和X年MM月DD日 or YYYY年MM月DD日 or YYYY/MM/DD
                    if re.match(r"(令和|平成|昭和)?\d{1,4}年\d{1,2}月\d{1,2}日", text):
                        metadata.decision_date = text
                    elif re.match(r"\d{4}/\d{1,2}/\d{1,2}", text):
                        metadata.decision_date = text
                    # Court names
                    elif any(court in text for court in ["裁判所", "最高裁", "高裁", "地裁", "簡裁", "家裁"]):
                        metadata.court = text
                    # Case number pattern (事件番号)
                    elif re.match(r"(令和|平成|昭和)?\d{1,4}[（(].+[）)]\d+", text):
                        metadata.case_number = text

                # Use link text as case title if nothing else
                link_text = link.get_text(strip=True)
                if link_text and len(link_text) > 3:
                    metadata.case_title = link_text

                cases.append(metadata)

            except Exception as e:
                logger.debug(f"Failed to parse result item: {e}")
                continue

        return cases

    def get_case_detail(self, metadata: CaseMetadata) -> Optional[CaseDetail]:
        """
        Fetch and parse the full detail page for a case.

        Discovered 2026-03-13 via Chrome exploration:
        ─────────────────────────────────────────────
        Detail page URL: /hanrei/{id}/detail2/index.html
        PDF full text:   /assets/hanrei/hanrei-pdf-{id}.pdf

        The detail page uses DL/DT/DD HTML structure for metadata:
          <dl>
            <dt>事件番号</dt><dd>令和5(オ)第1234号</dd>
            <dt>事件名</dt><dd>敷金返還等請求事件</dd>
            <dt>裁判年月日</dt><dd>令和6年3月15日</dd>
            <dt>法廷名</dt><dd>第二小法廷</dd>
            <dt>裁判種別</dt><dd>判決</dd>
            <dt>結果</dt><dd>破棄自判</dd>
            <dt>判示事項</dt><dd>...</dd>
            <dt>裁判要旨</dt><dd>...</dd>
            <dt>参照法条</dt><dd>民法第622条の2...</dd>
            <dt>全文</dt><dd><a href="...pdf">全文</a></dd>
          </dl>

        The full decision text is in a PDF, NOT inline HTML.
        We extract metadata from the DL/DT/DD structure and the
        裁判要旨 (summary/headnote) from the detail page itself.
        For full text analysis, we would need to download and parse
        the PDF — that's Phase 2 (requires pdfminer or similar).

        Extracts:
        - Case metadata (事件番号, 事件名, 裁判年月日, etc.)
        - 裁判要旨 (judicial summary — rich source of document/flaw references)
        - 判示事項 (matters decided)
        - Referenced statutes (参照法条)
        - Document references (contracts, forms cited)
        - Identified flaws/errors mentioned
        """
        if metadata.case_id in self.scraped_ids:
            logger.info(f"Skipping already-scraped case: {metadata.case_id}")
            return None

        try:
            time.sleep(REQUEST_DELAY)
            response = self.client.get(metadata.url)
            response.raise_for_status()

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch case {metadata.case_id}: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        detail = CaseDetail(
            metadata=metadata,
            scraped_at=datetime.now().isoformat(),
        )

        # ── Step 1: Extract metadata from DL/DT/DD structure ──
        dl_data = self._parse_dl_metadata(soup)

        # Update metadata from DL/DT/DD fields
        if dl_data.get("事件番号") and not metadata.case_number:
            metadata.case_number = dl_data["事件番号"]
        if dl_data.get("事件名") and not metadata.case_title:
            metadata.case_title = dl_data["事件名"]
        if dl_data.get("裁判年月日") and not metadata.decision_date:
            metadata.decision_date = dl_data["裁判年月日"]
        if dl_data.get("裁判所名") and not metadata.court:
            metadata.court = dl_data["裁判所名"]
        if dl_data.get("法廷名") and not metadata.court:
            metadata.court = dl_data["法廷名"]
        if dl_data.get("裁判種別"):
            metadata.case_type = dl_data["裁判種別"]

        # ── Step 2: Extract 裁判要旨 (judicial summary) ──
        # This is the richest text source on the detail page
        summary_text = dl_data.get("裁判要旨", "")
        matters_text = dl_data.get("判示事項", "")

        # ── Step 3: Extract 参照法条 (referenced statutes) from DL/DD ──
        statutes_text = dl_data.get("参照法条", "")

        # ── Step 4: Try to get full text from page content ──
        # Some cases have inline text, especially lower court decisions
        text_containers = (
            soup.select(".hanrei-text")
            or soup.select(".full-text")
            or soup.select("#hanreiFullText")
            or soup.select("div.mainContents")
        )

        if text_containers:
            detail.full_text = text_containers[0].get_text(separator="\n", strip=True)
        else:
            # Combine available text from DL/DD metadata
            # The 裁判要旨 + 判示事項 together are very informative
            combined_parts = []
            if matters_text:
                combined_parts.append(f"【判示事項】\n{matters_text}")
            if summary_text:
                combined_parts.append(f"【裁判要旨】\n{summary_text}")
            detail.full_text = "\n\n".join(combined_parts)

        # ── Step 5: Note PDF URL for later full-text extraction ──
        # Full text is typically in a PDF at /assets/hanrei/hanrei-pdf-{id}.pdf
        pdf_url = f"{BASE_URL}/assets/hanrei/hanrei-pdf-{metadata.case_id}.pdf"
        # Also check if the DL/DD has a direct PDF link
        fulltext_dd = dl_data.get("全文", "")
        if fulltext_dd:
            pdf_link = soup.find("dt", string=re.compile(r"全文"))
            if pdf_link:
                pdf_dd = pdf_link.find_next_sibling("dd")
                if pdf_dd:
                    pdf_a = pdf_dd.find("a", href=True)
                    if pdf_a:
                        href = pdf_a.get("href", "")
                        if href.startswith("/"):
                            pdf_url = BASE_URL + href
                        elif href.startswith("http"):
                            pdf_url = href

        # Store PDF URL in metadata for later Phase 2 extraction
        metadata.url = metadata.url  # Keep detail page URL
        # Store PDF URL as extra info in the full_text field marker
        if detail.full_text:
            detail.full_text += f"\n\n【PDF全文URL】{pdf_url}"
        else:
            detail.full_text = f"【PDF全文URL】{pdf_url}"

        # ── Step 6: Extract structured sections from available text ──
        analysis_text = f"{summary_text}\n{matters_text}\n{detail.full_text}"
        detail.judgment = self._extract_section(analysis_text, "主文")
        detail.reasoning = self._extract_section(analysis_text, "理由")
        detail.facts = self._extract_section(analysis_text, "事実")

        # ── Step 7: Extract referenced statutes ──
        if statutes_text:
            detail.referenced_statutes = [s.strip() for s in re.split(r"[、,\s]+", statutes_text) if s.strip()]
        detail.referenced_statutes += self._extract_statutes(analysis_text)
        detail.referenced_statutes = sorted(set(detail.referenced_statutes))

        # ── Step 8: Extract document references and flaws ──
        detail.document_references = self._extract_document_refs(analysis_text)
        detail.identified_flaws = self._extract_flaws(analysis_text)

        return detail

    def _parse_dl_metadata(self, soup: BeautifulSoup) -> dict[str, str]:
        """
        Parse the DL/DT/DD metadata structure on detail pages.

        The courts.go.jp detail pages use this HTML pattern:
          <dl>
            <dt>事件番号</dt><dd>...</dd>
            <dt>事件名</dt><dd>...</dd>
            ...
          </dl>

        Returns a dict mapping label → value text.
        """
        dl_data = {}
        for dl in soup.find_all("dl"):
            dts = dl.find_all("dt")
            for dt in dts:
                label = dt.get_text(strip=True)
                dd = dt.find_next_sibling("dd")
                if dd:
                    value = dd.get_text(separator=" ", strip=True)
                    dl_data[label] = value
        return dl_data

    def _extract_section(self, full_text: str, section_name: str) -> str:
        """Extract a named section from the full decision text."""
        # Common patterns for section headers in Japanese court decisions
        patterns = [
            rf"{section_name}\s*\n(.*?)(?=\n(?:主文|理由|事実|事実及び理由|結論|当裁判所の判断)\s*\n|\Z)",
            rf"第?\d*\s*{section_name}(.*?)(?=第?\d*\s*(?:主文|理由|事実|結論)|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, full_text, re.DOTALL)
            if match:
                return match.group(1).strip()[:5000]  # Cap at 5k chars

        return ""

    def _extract_statutes(self, text: str) -> list[str]:
        """Extract references to legal statutes from decision text."""
        statute_patterns = [
            r"民法第?\d+条(?:の\d+)?(?:第\d+項)?",       # Civil Code
            r"借地借家法第?\d+条(?:の\d+)?",               # Land & Building Lease Act
            r"建築基準法第?\d+条(?:の\d+)?",               # Building Standards Act
            r"住宅の品質確保の促進等に関する法律第?\d+条", # Housing Quality Act
            r"消費者契約法第?\d+条",                       # Consumer Contract Act
            r"宅地建物取引業法第?\d+条",                   # Real Estate Transactions Act
            r"不動産登記法第?\d+条",                       # Real Estate Registration Act
            r"区分所有法第?\d+条",                         # Condominium Ownership Act
        ]

        statutes = set()
        for pattern in statute_patterns:
            for match in re.finditer(pattern, text):
                statutes.add(match.group())

        return sorted(statutes)

    def _extract_document_refs(self, text: str) -> list[str]:
        """
        Extract references to real-world documents cited in the decision.

        These are the goldmine — actual document types that appear in disputes.
        """
        doc_patterns = [
            # Contracts
            r"賃貸借契約書",        # Lease agreement
            r"売買契約書",          # Sales agreement
            r"請負契約書",          # Construction contract
            r"保証契約書",          # Guarantor contract
            r"媒介契約書",          # Brokerage contract
            # Forms and notices
            r"重要事項説明書",      # Important matters disclosure
            r"建物状況調査報告書",  # Building inspection report
            r"管理規約",            # Management rules
            r"使用細則",            # Usage regulations
            r"退去通知書?",         # Eviction notice
            r"催告書",              # Demand letter
            r"解約通知",            # Cancellation notice
            r"更新通知",            # Renewal notice
            # Financial
            r"敷金精算書",          # Security deposit settlement
            r"原状回復費用明細",    # Restoration cost breakdown
            r"修繕費用見積",        # Repair cost estimate
            r"賃料通知",            # Rent notification
            # Registration
            r"不動産登記簿",        # Property registration book
            r"登記事項証明書",      # Registration certificate
            r"固定資産評価証明書",  # Property tax assessment certificate
            # Housing specific
            r"入居申込書",          # Move-in application
            r"住宅管理申請書?",     # Housing management application
            r"建物検査報告書?",     # Building inspection report
        ]

        refs = set()
        for pattern in doc_patterns:
            if re.search(pattern, text):
                refs.add(re.search(pattern, text).group())

        return sorted(refs)

    def _extract_flaws(self, text: str) -> list[str]:
        """
        Extract mentions of document flaws, errors, and defects from decisions.

        These patterns represent what courts found wrong with submitted documents —
        exactly the error patterns we want to inject into synthetic data.
        """
        flaw_patterns = [
            # Missing/incomplete
            (r"記載(?:が|の)不(?:十分|備|足)", "incomplete_entry"),
            (r"記載漏れ", "missing_entry"),
            (r"記入(?:が|の)?(?:ない|なかった|不備)", "unfilled_field"),
            (r"署名(?:が|の)?(?:ない|欠けて|不備)", "missing_signature"),
            (r"押印(?:が|の)?(?:ない|欠けて|不備)", "missing_seal"),
            # Incorrect/invalid
            (r"記載(?:が|の)?(?:誤り|誤って|不正確)", "incorrect_entry"),
            (r"計算(?:が|の)?(?:誤り|間違|不正確)", "calculation_error"),
            (r"日付(?:が|の)?(?:誤り|間違|不正確)", "date_error"),
            (r"金額(?:が|の)?(?:誤り|間違|不正確|相違)", "amount_error"),
            # Contradictions
            (r"矛盾(?:する|して|が)", "contradiction"),
            (r"整合性(?:が|を)(?:欠|なく)", "inconsistency"),
            (r"食い違い", "discrepancy"),
            # Legal defects
            (r"法的(?:に)?(?:無効|不備|瑕疵)", "legal_defect"),
            (r"要件(?:を|が)(?:欠|充た[さず])", "missing_requirement"),
            (r"形式(?:的)?(?:に)?(?:不備|瑕疵)", "formal_defect"),
            # Document quality
            (r"判読(?:が)?(?:困難|できな)", "illegible"),
            (r"不鮮明", "unclear_image"),
            (r"改ざん", "falsification"),
            (r"偽造", "forgery"),
        ]

        flaws = []
        for pattern, flaw_type in flaw_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Get surrounding context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].replace("\n", " ")
                flaws.append({
                    "type": flaw_type,
                    "match": match.group(),
                    "context": context,
                })

        return flaws

    def _enrich_metadata(self, soup: BeautifulSoup, metadata: CaseMetadata):
        """
        Extract additional metadata from the detail page.

        Uses DL/DT/DD structure (primary) and falls back to other
        patterns (TH/TD, labeled spans) if DL is not found.
        """
        # Primary: DL/DT/DD structure (confirmed on courts.go.jp)
        dl_data = self._parse_dl_metadata(soup)
        if dl_data:
            if dl_data.get("事件番号") and not metadata.case_number:
                metadata.case_number = dl_data["事件番号"]
            if dl_data.get("裁判年月日") and not metadata.decision_date:
                metadata.decision_date = dl_data["裁判年月日"]
            if dl_data.get("裁判所名") and not metadata.court:
                metadata.court = dl_data["裁判所名"]
            if dl_data.get("法廷名") and not metadata.court:
                metadata.court = dl_data["法廷名"]
            if dl_data.get("事件名") and not metadata.case_title:
                metadata.case_title = dl_data["事件名"]
            return  # DL/DT/DD found, no need for fallback

        # Fallback: look for TH/TD or labeled span patterns
        for label_text in ["事件番号", "裁判年月日", "裁判所名", "事件名"]:
            label = soup.find(string=re.compile(label_text))
            if label:
                parent = label.find_parent(["th", "dt", "span", "div"])
                if parent:
                    value_elem = parent.find_next_sibling(["td", "dd", "span", "div"])
                    if value_elem:
                        value = value_elem.get_text(strip=True)
                        if label_text == "事件番号" and not metadata.case_number:
                            metadata.case_number = value
                        elif label_text == "裁判年月日" and not metadata.decision_date:
                            metadata.decision_date = value
                        elif label_text == "裁判所名" and not metadata.court:
                            metadata.court = value
                        elif label_text == "事件名" and not metadata.case_title:
                            metadata.case_title = value

    def save_case(self, detail: CaseDetail):
        """Save a scraped case to JSONL output and update progress."""
        output_file = self.output_dir / f"cases_{detail.metadata.category or 'general'}.jsonl"

        record = {
            "metadata": asdict(detail.metadata),
            "full_text": detail.full_text,
            "judgment": detail.judgment,
            "reasoning": detail.reasoning,
            "facts": detail.facts,
            "referenced_statutes": detail.referenced_statutes,
            "document_references": detail.document_references,
            "identified_flaws": detail.identified_flaws,
            "scraped_at": detail.scraped_at,
        }

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Update progress
        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "case_id": detail.metadata.case_id,
                "category": detail.metadata.category,
                "url": detail.metadata.url,
                "scraped_at": detail.scraped_at,
            }, ensure_ascii=False) + "\n")

        self.scraped_ids.add(detail.metadata.case_id)

    def bulk_scrape(self, max_per_query: int = 30):
        """
        Run all predefined real estate queries.

        This is the main entry point for building the training corpus.
        """
        total_scraped = 0
        total_flaws = 0
        total_doc_refs = 0

        for query_def in REAL_ESTATE_QUERIES:
            keyword = query_def["keyword"]
            category = query_def["category"]

            logger.info(f"\n{'='*60}")
            logger.info(f"QUERY: {keyword} (category: {category})")
            logger.info(f"{'='*60}")

            cases = self.search(keyword, max_results=max_per_query)
            logger.info(f"Found {len(cases)} cases")

            for i, case_meta in enumerate(cases):
                case_meta.category = category

                if case_meta.case_id in self.scraped_ids:
                    logger.info(f"  [{i+1}/{len(cases)}] Skipping (already scraped): {case_meta.case_id}")
                    continue

                logger.info(f"  [{i+1}/{len(cases)}] Fetching: {case_meta.case_id} - {case_meta.case_title[:40]}")

                detail = self.get_case_detail(case_meta)
                if detail:
                    self.save_case(detail)
                    total_scraped += 1
                    total_flaws += len(detail.identified_flaws)
                    total_doc_refs += len(detail.document_references)

                    if detail.identified_flaws:
                        logger.info(f"    Flaws found: {len(detail.identified_flaws)}")
                        for flaw in detail.identified_flaws[:3]:
                            logger.info(f"      - {flaw['type']}: {flaw['match']}")

                    if detail.document_references:
                        logger.info(f"    Document refs: {', '.join(detail.document_references[:5])}")

        logger.info(f"\n{'='*60}")
        logger.info(f"BULK SCRAPE COMPLETE")
        logger.info(f"  Cases scraped: {total_scraped}")
        logger.info(f"  Total flaws identified: {total_flaws}")
        logger.info(f"  Total document references: {total_doc_refs}")
        logger.info(f"  Output directory: {self.output_dir}")
        logger.info(f"{'='*60}")

    def generate_flaw_taxonomy(self):
        """
        Analyze all scraped cases and generate a flaw taxonomy report.

        This produces the YAML-compatible error injection config
        derived from actual court findings.
        """
        flaw_counts: dict[str, int] = {}
        flaw_examples: dict[str, list[str]] = {}
        doc_ref_counts: dict[str, int] = {}

        for jsonl_file in self.output_dir.glob("cases_*.jsonl"):
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)

                    for flaw in record.get("identified_flaws", []):
                        ftype = flaw["type"]
                        flaw_counts[ftype] = flaw_counts.get(ftype, 0) + 1
                        if ftype not in flaw_examples:
                            flaw_examples[ftype] = []
                        if len(flaw_examples[ftype]) < 5:
                            flaw_examples[ftype].append(flaw["context"])

                    for ref in record.get("document_references", []):
                        doc_ref_counts[ref] = doc_ref_counts.get(ref, 0) + 1

        # Generate taxonomy report
        report = {
            "generated_at": datetime.now().isoformat(),
            "flaw_taxonomy": {
                ftype: {
                    "count": count,
                    "examples": flaw_examples.get(ftype, []),
                }
                for ftype, count in sorted(
                    flaw_counts.items(), key=lambda x: -x[1]
                )
            },
            "document_types_referenced": {
                ref: count
                for ref, count in sorted(
                    doc_ref_counts.items(), key=lambda x: -x[1]
                )
            },
        }

        report_path = self.output_dir / "flaw_taxonomy.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Flaw taxonomy written to: {report_path}")
        logger.info(f"Flaw types found: {len(flaw_counts)}")
        logger.info(f"Document types referenced: {len(doc_ref_counts)}")

        return report

    def close(self):
        """Close the HTTP client."""
        self.client.close()


# ─── CLI ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Japan Court Case Scraper for Real Estate Disputes"
    )
    parser.add_argument(
        "--search", type=str,
        help="Search keyword (Japanese)",
    )
    parser.add_argument(
        "--court", type=str, default="",
        choices=["", "supreme", "high", "district", "summary"],
        help="Filter by court type",
    )
    parser.add_argument(
        "--date-from", type=str, default="",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--date-to", type=str, default="",
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--max-results", type=int, default=50,
        help="Maximum results per query (default: 50)",
    )
    parser.add_argument(
        "--bulk", action="store_true",
        help="Run all predefined real estate queries",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from progress file (skip already-scraped cases)",
    )
    parser.add_argument(
        "--taxonomy", action="store_true",
        help="Generate flaw taxonomy from scraped data",
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )

    args = parser.parse_args()

    scraper = JapanCourtScraper(output_dir=args.output)

    try:
        if args.taxonomy:
            scraper.generate_flaw_taxonomy()
        elif args.bulk:
            scraper.bulk_scrape(max_per_query=args.max_results)
            scraper.generate_flaw_taxonomy()
        elif args.search:
            cases = scraper.search(
                args.search,
                court_type=args.court,
                date_from=args.date_from,
                date_to=args.date_to,
                max_results=args.max_results,
            )
            for i, case_meta in enumerate(cases):
                logger.info(f"[{i+1}/{len(cases)}] Fetching: {case_meta.case_id}")
                detail = scraper.get_case_detail(case_meta)
                if detail:
                    scraper.save_case(detail)
        else:
            parser.print_help()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
