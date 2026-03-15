#!/usr/bin/env python3
"""
Germany Court Decision Scraper — OpenJur, dejure.org, Open Legal Data

Scrapes Mietrecht and real estate dispute decisions from German court
databases to extract:
- Document structure patterns (how real contracts/forms are referenced)
- Flaw taxonomies (what errors courts identify in Mietverträge, Nebenkostenabrechnungen)
- Domain-specific legal vocabulary

Primary targets:
1. Open Legal Data API (openlegaldata.io) — REST API, easiest programmatic access
2. dejure.org — BGB §535-580a cross-references to find Mietrecht decisions
3. OpenJur.de — broad search with full-text access

Legal basis:
- German court decisions are public records
- §60d UrhG permits text/data mining for non-commercial research
- BGH has ruled web scraping legal when robots.txt is respected

Usage:
    python germany_courts.py --source oldp --search "Nebenkostenabrechnung" --max 50
    python germany_courts.py --source dejure --section 535
    python germany_courts.py --bulk  # Run all predefined Mietrecht queries
    python germany_courts.py --taxonomy  # Generate flaw taxonomy from scraped data

Rate limiting: 3-5 second delays between requests.
"""

from __future__ import annotations
import argparse
import json
import logging
import re
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

REQUEST_DELAY = 4.0
TIMEOUT = 30.0
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "germany"

# Open Legal Data API (best programmatic access)
OLDP_API_BASE = "https://de.openlegaldata.io/api"

# dejure.org base URLs
DEJURE_BASE = "https://dejure.org"
DEJURE_BGB = f"{DEJURE_BASE}/gesetze/BGB"

# OpenJur base URL
OPENJUR_BASE = "https://openjur.de"

# Mietrecht BGB sections (§535-580a)
MIETRECHT_SECTIONS = list(range(535, 581))

# Search queries organized by category
MIETRECHT_QUERIES = [
    # Core lease disputes
    {"keyword": "Mietvertrag Mangel", "category": "lease_defect"},
    {"keyword": "Mietvertrag ungültig", "category": "lease_invalid"},
    {"keyword": "Mietvertrag Kündigung unwirksam", "category": "termination_invalid"},
    # Nebenkostenabrechnung (the most document-heavy category)
    {"keyword": "Nebenkostenabrechnung fehlerhaft", "category": "utility_bill_error"},
    {"keyword": "Nebenkostenabrechnung Frist", "category": "utility_bill_deadline"},
    {"keyword": "Nebenkostenabrechnung formell", "category": "utility_bill_formal"},
    {"keyword": "Betriebskostenabrechnung", "category": "operating_cost_statement"},
    {"keyword": "Betriebskosten Umlageschlüssel", "category": "cost_allocation_key"},
    # Security deposit
    {"keyword": "Mietkaution Abrechnung", "category": "deposit_settlement"},
    {"keyword": "Kaution Rückzahlung", "category": "deposit_return"},
    # Rent reduction / defects
    {"keyword": "Mietminderung Schimmel", "category": "rent_reduction_mold"},
    {"keyword": "Mietminderung Mangel", "category": "rent_reduction_defect"},
    {"keyword": "Mietmangel Heizung", "category": "heating_defect"},
    # Cosmetic repairs (Schönheitsreparaturen — massive caseload)
    {"keyword": "Schönheitsreparaturen unwirksam", "category": "cosmetic_repairs"},
    {"keyword": "Renovierung Auszug", "category": "move_out_renovation"},
    # Handover protocol
    {"keyword": "Übergabeprotokoll", "category": "handover_protocol"},
    {"keyword": "Wohnungsübergabe Mängel", "category": "handover_defects"},
    # Rent increase
    {"keyword": "Mieterhöhung formell unwirksam", "category": "rent_increase_formal"},
    {"keyword": "Mietspiegel", "category": "rent_index"},
    # Real estate purchase
    {"keyword": "Kaufvertrag Immobilie Mangel", "category": "purchase_defect"},
    {"keyword": "Grundstückskaufvertrag", "category": "land_purchase"},
    # Building defects
    {"keyword": "Baumangel Gewährleistung", "category": "construction_defect"},
    {"keyword": "Werkvertrag Bauvertrag Mangel", "category": "construction_contract"},
    # WEG (Wohnungseigentümergemeinschaft)
    {"keyword": "WEG Beschluss anfechtbar", "category": "weg_resolution"},
    {"keyword": "Hausgeld Abrechnung", "category": "weg_maintenance_fee"},
]


# ─── Data Models ──────────────────────────────────────────────────

@dataclass
class DECaseMetadata:
    """Metadata for a German court case."""
    case_id: str = ""
    aktenzeichen: str = ""         # Case file number (e.g., VIII ZR 184/23)
    court: str = ""                # Gericht
    decision_date: str = ""        # Entscheidungsdatum
    case_title: str = ""           # Kurzbezeichnung
    ecli: str = ""                 # European Case Law Identifier
    url: str = ""
    source: str = ""               # Which database
    search_query: str = ""
    category: str = ""

@dataclass
class DECaseDetail:
    """Full detail of a German court decision."""
    metadata: DECaseMetadata
    full_text: str = ""
    tenor: str = ""                # Urteilstenor (judgment)
    tatbestand: str = ""           # Tatbestand (facts)
    gruende: str = ""              # Entscheidungsgründe (reasoning)
    leitsatz: str = ""             # Leitsatz (headnote/key principle)
    referenced_sections: list = field(default_factory=list)  # BGB §§
    document_references: list = field(default_factory=list)
    identified_flaws: list = field(default_factory=list)
    scraped_at: str = ""


# ─── Open Legal Data API Scraper ─────────────────────────────────

class OLDPScraper:
    """
    Scraper using the Open Legal Data REST API.

    This is the cleanest data source — proper API with JSON responses.
    Dataset: 251,000+ German court decisions with full text.

    API docs: https://de.openlegaldata.io/api/
    """

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            timeout=TIMEOUT,
            headers={
                "User-Agent": "VilseckKI-Research/1.0 (academic; workflow.tools@icloud.com)",
                "Accept": "application/json",
            },
        )
        self.progress_file = output_dir / ".progress_oldp.jsonl"
        self.scraped_ids: set[str] = set()
        self._load_progress()

    def _load_progress(self):
        if self.progress_file.exists():
            with open(self.progress_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            self.scraped_ids.add(str(data.get("case_id", "")))
                        except json.JSONDecodeError:
                            continue
            logger.info(f"OLDP: Loaded {len(self.scraped_ids)} previously scraped cases")

    def search(
        self,
        keyword: str,
        court_slug: str = "",
        max_results: int = 50,
    ) -> list[dict]:
        """
        Search via OLDP REST API.

        API endpoint: GET /api/cases/search/?q={keyword}
        """
        results = []
        page = 1
        per_page = 20  # API default

        while len(results) < max_results:
            try:
                params = {
                    "q": keyword,
                    "page": page,
                    "page_size": min(per_page, max_results - len(results)),
                }
                if court_slug:
                    params["court__slug"] = court_slug

                response = self.client.get(
                    f"{OLDP_API_BASE}/cases/search/",
                    params=params,
                )

                if response.status_code == 404:
                    # Try alternative endpoint
                    response = self.client.get(
                        f"{OLDP_API_BASE}/cases/",
                        params=params,
                    )

                response.raise_for_status()
                data = response.json()

                # Handle paginated response
                if isinstance(data, dict):
                    items = data.get("results", data.get("items", []))
                    if not items:
                        break
                    results.extend(items)
                    if not data.get("next"):
                        break
                elif isinstance(data, list):
                    if not data:
                        break
                    results.extend(data)
                else:
                    break

                page += 1
                time.sleep(REQUEST_DELAY)

            except httpx.HTTPError as e:
                logger.error(f"OLDP search failed: {e}")
                break

        return results[:max_results]

    def process_case(self, case_data: dict, category: str = "", query: str = "") -> Optional[DECaseDetail]:
        """Process a case from the API response into our format."""
        case_id = str(case_data.get("id", case_data.get("slug", "")))

        if case_id in self.scraped_ids:
            return None

        metadata = DECaseMetadata(
            case_id=case_id,
            aktenzeichen=case_data.get("file_number", ""),
            court=case_data.get("court", {}).get("name", "") if isinstance(case_data.get("court"), dict) else str(case_data.get("court", "")),
            decision_date=case_data.get("date", ""),
            case_title=case_data.get("title", case_data.get("name", "")),
            ecli=case_data.get("ecli", ""),
            url=case_data.get("url", case_data.get("source_url", "")),
            source="openlegaldata",
            search_query=query,
            category=category,
        )

        full_text = case_data.get("content", case_data.get("text", ""))
        if not full_text:
            # Try to fetch full text
            detail_url = case_data.get("url", "")
            if detail_url and detail_url.startswith("http"):
                try:
                    time.sleep(REQUEST_DELAY)
                    resp = self.client.get(detail_url)
                    resp.raise_for_status()
                    detail_data = resp.json()
                    full_text = detail_data.get("content", "")
                except Exception:
                    pass

        detail = DECaseDetail(
            metadata=metadata,
            full_text=full_text,
            scraped_at=datetime.now().isoformat(),
        )

        if full_text:
            detail.tenor = self._extract_section(full_text, "Tenor")
            detail.tatbestand = self._extract_section(full_text, "Tatbestand")
            detail.gruende = self._extract_section(full_text, "Entscheidungsgründe")
            detail.leitsatz = self._extract_section(full_text, "Leitsatz")
            detail.referenced_sections = _extract_bgb_sections(full_text)
            detail.document_references = _extract_de_document_refs(full_text)
            detail.identified_flaws = _extract_de_flaws(full_text)

        return detail

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a named section from the decision text."""
        patterns = [
            rf"(?:^|\n)\s*{section_name}\s*\n(.*?)(?=\n\s*(?:Tenor|Tatbestand|Entscheidungsgründe|Gründe|Leitsatz)\s*\n|\Z)",
            rf"(?:^|\n)\s*(?:I+\.?\s*)?{section_name}:?\s*\n(.*?)(?=\n\s*(?:I+\.?\s*)?(?:Tenor|Tatbestand|Entscheidungsgründe|Gründe)\s*\n|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()[:5000]

        return ""

    def close(self):
        self.client.close()


# ─── DeJure Scraper ───────────────────────────────────────────────

class DeJureScraper:
    """
    Scraper for dejure.org — follows BGB section references to find cases.

    Strategy: Start from Mietrecht BGB sections (§535-580a), use the
    paginated decision list pages to collect case metadata, then follow
    links to full-text sources (openjur.de, bundesgerichtshof.de, etc.)

    URL patterns (confirmed via live site exploration 2026-03-13):
    ─────────────────────────────────────────────────────────────
    BGB section page:     /gesetze/BGB/{section}.html
    Paginated case list:  /dienste/lex/BGB/{section}/{page}.html
                          (50 cases per page, pages numbered from 1)
    Case redirect link:   /dienste/vernetzung/rechtsprechung?Gericht=...&Datum=...&Aktenzeichen=...
                          (redirects to full-text source like openjur.de)
    Case detail page:     /dienste/vernetzung/rechtsprechung?Gericht=BGH&Datum=06.08.2025&Aktenzeichen=VIII%20ZR%20250/23

    Case detail sections (on dejure case page):
    - Volltextveröffentlichungen — links to full-text sources
    - Kurzfassungen/Presse — summaries
    - Verfahrensgang — procedural history
    - Papierfundstellen — print references
    - Zitiert selbst / Wird zitiert von — citation network

    HTML structure for case list pages:
    <ul>
      <li>
        <a href="/dienste/vernetzung/rechtsprechung?Gericht=...&Datum=...&Aktenzeichen=...">
          OLG München, 12.02.2026 - 14 U 1880/25
        </a>
        <p class="kursiv">Nebenkostenabrechnung, Gewerberaummietvertrag, ...</p>
      </li>
    </ul>

    Note: dejure.org does NOT host full decision text itself.
    It aggregates links to openjur.de, bundesgerichtshof.de,
    rechtsinformationen.bund.de, rechtsprechung-im-internet.de, etc.
    For full text, we follow those links.
    """

    # Full-text source domains we follow from dejure case detail pages
    FULLTEXT_SOURCES = [
        "openjur.de",
        "bundesgerichtshof.de",
        "rechtsprechung-im-internet.de",
        "rechtsinformationen.bund.de",
        "landesrecht.rlp.de",
        "justiz.nrw.de",
    ]

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            timeout=TIMEOUT,
            headers={
                "User-Agent": "VilseckKI-Research/1.0 (academic; workflow.tools@icloud.com)",
                "Accept-Language": "de,en;q=0.5",
            },
            follow_redirects=True,
        )
        self.progress_file = output_dir / ".progress_dejure.jsonl"
        self.scraped_urls: set[str] = set()
        self._load_progress()

    def _load_progress(self):
        if self.progress_file.exists():
            with open(self.progress_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            self.scraped_urls.add(data.get("url", ""))
                        except json.JSONDecodeError:
                            continue
            logger.info(f"DeJure: Loaded {len(self.scraped_urls)} previously scraped")

    def get_cases_for_section(self, section_num: int, max_cases: int = 50, max_pages: int = 3) -> list[DECaseMetadata]:
        """
        Get court decisions citing a specific BGB section.

        Uses the paginated list pages at /dienste/lex/BGB/{section}/{page}.html
        which show 50 cases per page in a UL > LI structure.
        Each LI contains an <a> with court+date+case number and a
        <p class="kursiv"> with topic keywords.

        For §535 alone there are 7,045 decisions across 141 pages.
        We limit to max_pages to be respectful.
        """
        cases = []

        for page in range(1, max_pages + 1):
            if len(cases) >= max_cases:
                break

            url = f"{DEJURE_BASE}/dienste/lex/BGB/{section_num}/{page}.html"
            logger.info(f"Fetching decisions for BGB §{section_num}, page {page}: {url}")

            try:
                time.sleep(REQUEST_DELAY)
                response = self.client.get(url)
                if response.status_code == 404:
                    logger.info(f"  No more pages for §{section_num}")
                    break
                response.raise_for_status()
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch BGB §{section_num} page {page}: {e}")
                break

            soup = BeautifulSoup(response.text, "html.parser")

            # Find case links — they use the redirect URL pattern
            # Structure: UL > LI > A (case link) + P.kursiv (keywords)
            decision_links = soup.find_all("a", href=re.compile(
                r"/dienste/vernetzung/rechtsprechung\?"
            ))

            if not decision_links:
                logger.info(f"  No case links found on page {page}")
                break

            for link in decision_links:
                if len(cases) >= max_cases:
                    break

                href = link.get("href", "")
                if not href:
                    continue

                full_url = href if href.startswith("http") else DEJURE_BASE + href

                # Parse Gericht, Datum, Aktenzeichen from URL params
                params = {}
                if "?" in full_url:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(full_url)
                    for k, v in parse_qs(parsed.query).items():
                        params[k] = v[0] if v else ""

                # Extract topic keywords from the sibling <p class="kursiv">
                keywords = ""
                parent_li = link.find_parent("li")
                if parent_li:
                    kursiv_p = parent_li.find("p", class_="kursiv")
                    if kursiv_p:
                        keywords = kursiv_p.get_text(strip=True)

                link_text = link.get_text(strip=True)

                metadata = DECaseMetadata(
                    case_id=f"dejure_{section_num}_{len(cases)}",
                    aktenzeichen=params.get("Aktenzeichen", ""),
                    court=params.get("Gericht", ""),
                    decision_date=params.get("Datum", ""),
                    case_title=f"{link_text} — {keywords}"[:200] if keywords else link_text[:200],
                    url=full_url,
                    source="dejure",
                    search_query=f"BGB §{section_num}",
                    category=f"bgb_{section_num}",
                )
                cases.append(metadata)

            logger.info(f"  Page {page}: found {len(decision_links)} links, total so far: {len(cases)}")

        logger.info(f"  Total for §{section_num}: {len(cases)} decisions")
        return cases

    def get_case_detail(self, metadata: DECaseMetadata) -> Optional[DECaseDetail]:
        """
        Fetch full decision text via dejure.org case page.

        dejure.org case pages don't contain full text themselves.
        Instead they list "Volltextveröffentlichungen" — links to
        full-text sources like openjur.de or bundesgerichtshof.de.

        Strategy:
        1. Fetch dejure case page
        2. Extract Volltextveröffentlichungen links
        3. Follow the first available full-text link to get actual text
        4. Also extract the case's own metadata (citations, procedure)
        """
        if metadata.url in self.scraped_urls:
            return None

        # Step 1: Fetch dejure case detail page
        try:
            time.sleep(REQUEST_DELAY)
            response = self.client.get(metadata.url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch case from dejure: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Step 2: Extract full-text source links
        # The "Volltextveröffentlichungen" section contains links to actual texts
        fulltext_links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            # Check if link points to a known full-text source
            for source_domain in self.FULLTEXT_SOURCES:
                if source_domain in href:
                    fulltext_links.append({
                        "url": href if href.startswith("http") else "https:" + href,
                        "source": source_domain,
                        "text": a.get_text(strip=True),
                    })
                    break

        # Step 3: Extract any citation data from the dejure page itself
        # "Zitiert selbst" section contains references to other cases
        cited_cases = []
        for a in soup.find_all("a", href=re.compile(r"/dienste/vernetzung/rechtsprechung\?")):
            link_text = a.get_text(strip=True)
            if link_text and link_text != metadata.case_title:
                cited_cases.append(link_text[:100])

        # Step 4: Follow first full-text link to get actual decision text
        full_text = ""
        fulltext_source = ""

        for ft_link in fulltext_links:
            try:
                time.sleep(REQUEST_DELAY)
                ft_response = self.client.get(ft_link["url"])
                ft_response.raise_for_status()

                ft_soup = BeautifulSoup(ft_response.text, "html.parser")

                # Try various content selectors depending on source
                text_container = None
                if "openjur" in ft_link["source"]:
                    text_container = ft_soup.select_one("div.docbody") or ft_soup.select_one("div.document")
                elif "bundesgerichtshof" in ft_link["source"]:
                    text_container = ft_soup.select_one("div.docbody") or ft_soup.select_one("div.content")
                else:
                    text_container = (
                        ft_soup.select_one("div.docbody")
                        or ft_soup.select_one("div.document")
                        or ft_soup.select_one("article")
                        or ft_soup.select_one("main")
                        or ft_soup.select_one("div.content")
                    )

                if text_container:
                    full_text = text_container.get_text(separator="\n", strip=True)
                    fulltext_source = ft_link["source"]

                if full_text and len(full_text) > 200:
                    break  # Got good text, stop trying other sources

            except Exception as e:
                logger.debug(f"  Failed to fetch full text from {ft_link['source']}: {e}")
                continue

        # If we still don't have full text, try to extract from dejure page body
        if not full_text or len(full_text) < 100:
            body = soup.find("body")
            if body:
                full_text = body.get_text(separator="\n", strip=True)
                fulltext_source = "dejure_page"

        detail = DECaseDetail(
            metadata=metadata,
            full_text=full_text,
            scraped_at=datetime.now().isoformat(),
        )

        # Update metadata with source info
        if fulltext_source:
            detail.metadata.source = f"dejure→{fulltext_source}"

        if full_text:
            detail.referenced_sections = _extract_bgb_sections(full_text)
            detail.document_references = _extract_de_document_refs(full_text)
            detail.identified_flaws = _extract_de_flaws(full_text)

        return detail

    def scrape_mietrecht_sections(self, max_cases_per_section: int = 10):
        """Scrape decisions for all Mietrecht BGB sections."""
        for section in MIETRECHT_SECTIONS:
            cases = self.get_cases_for_section(section, max_cases=max_cases_per_section)
            for case_meta in cases:
                detail = self.get_case_detail(case_meta)
                if detail and detail.full_text:
                    self._save(detail)

    def _save(self, detail: DECaseDetail):
        """Save case to output."""
        out_file = self.output_dir / f"dejure_{detail.metadata.category}.jsonl"
        record = {
            "metadata": asdict(detail.metadata),
            "full_text": detail.full_text[:10000],  # Cap size
            "fulltext_links_found": len([
                a for a in detail.metadata.url.split("&")
            ]) if detail.metadata.url else 0,
            "referenced_sections": detail.referenced_sections,
            "document_references": detail.document_references,
            "identified_flaws": detail.identified_flaws,
            "scraped_at": detail.scraped_at,
        }
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "url": detail.metadata.url,
                "category": detail.metadata.category,
                "scraped_at": detail.scraped_at,
            }, ensure_ascii=False) + "\n")

        self.scraped_urls.add(detail.metadata.url)

    def close(self):
        self.client.close()


# ─── OpenJur Scraper ──────────────────────────────────────────────

class OpenJurScraper:
    """
    Scraper for OpenJur.de — keyword-based full-text search.

    OpenJur is the largest free German case law database.
    """

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            timeout=TIMEOUT,
            headers={
                "User-Agent": "VilseckKI-Research/1.0 (academic; workflow.tools@icloud.com)",
                "Accept-Language": "de,en;q=0.5",
            },
            follow_redirects=True,
        )
        self.progress_file = output_dir / ".progress_openjur.jsonl"
        self.scraped_ids: set[str] = set()
        self._load_progress()

    def _load_progress(self):
        if self.progress_file.exists():
            with open(self.progress_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            self.scraped_ids.add(data.get("case_id", ""))
                        except json.JSONDecodeError:
                            continue

    def search(self, keyword: str, max_results: int = 50) -> list[DECaseMetadata]:
        """Search OpenJur for cases matching keyword.

        OpenJur search URL: /suche/?searchPhrase={keyword}
        Also supports: /suche/?q={keyword} (older format)
        Results page shows cases in <article> or <div.result> elements.
        Case detail URL pattern: /u/{case_id}.html
        """
        cases = []
        page = 1

        while len(cases) < max_results:
            try:
                # OpenJur search URL — uses searchPhrase param
                url = f"{OPENJUR_BASE}/suche/"
                params = {"searchPhrase": keyword, "page": page}

                time.sleep(REQUEST_DELAY)
                response = self.client.get(url, params=params)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Find result entries
                result_items = (
                    soup.select("div.result")
                    or soup.select("li.result")
                    or soup.select("div.search-result")
                    or soup.select("article")
                )

                if not result_items:
                    break

                for item in result_items:
                    link = item.find("a", href=True)
                    if not link:
                        continue

                    href = link.get("href", "")
                    full_url = href if href.startswith("http") else OPENJUR_BASE + href

                    # Extract case ID from URL (usually /u/XXXXXX.html)
                    id_match = re.search(r"/u/(\d+)", href)
                    case_id = id_match.group(1) if id_match else href

                    title = link.get_text(strip=True)

                    # Look for metadata in the result item
                    meta_text = item.get_text(separator=" ", strip=True)
                    court = ""
                    date = ""

                    # Common German court abbreviations
                    court_match = re.search(
                        r"(BGH|BVerfG|OLG|LG|AG|BAG|BVerwG|BSG|BFH)\s+[\w\-]+",
                        meta_text
                    )
                    if court_match:
                        court = court_match.group()

                    date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", meta_text)
                    if date_match:
                        date = date_match.group()

                    az_match = re.search(
                        r"(?:Az\.?:?\s*)?((?:I+V?|VI+|XI+|XI?I?)\s+Z[RB]\s+\d+/\d+|\d+\s+[A-Z]\s+\d+/\d+)",
                        meta_text,
                    )
                    aktenzeichen = az_match.group(1) if az_match else ""

                    metadata = DECaseMetadata(
                        case_id=case_id,
                        aktenzeichen=aktenzeichen,
                        court=court,
                        decision_date=date,
                        case_title=title[:200],
                        url=full_url,
                        source="openjur",
                        search_query=keyword,
                    )
                    cases.append(metadata)

                page += 1

            except httpx.HTTPError as e:
                logger.error(f"OpenJur search failed: {e}")
                break

        return cases[:max_results]

    def get_case_detail(self, metadata: DECaseMetadata) -> Optional[DECaseDetail]:
        """Fetch full case text from OpenJur."""
        if metadata.case_id in self.scraped_ids:
            return None

        try:
            time.sleep(REQUEST_DELAY)
            response = self.client.get(metadata.url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        text_container = (
            soup.select("div.docbody")
            or soup.select("div.document")
            or soup.select("div.content")
            or soup.select("main")
        )

        full_text = ""
        if text_container:
            full_text = text_container[0].get_text(separator="\n", strip=True)

        detail = DECaseDetail(
            metadata=metadata,
            full_text=full_text,
            scraped_at=datetime.now().isoformat(),
        )

        if full_text:
            detail.referenced_sections = _extract_bgb_sections(full_text)
            detail.document_references = _extract_de_document_refs(full_text)
            detail.identified_flaws = _extract_de_flaws(full_text)

        return detail

    def _save(self, detail: DECaseDetail):
        out_file = self.output_dir / f"openjur_{detail.metadata.category}.jsonl"
        record = {
            "metadata": asdict(detail.metadata),
            "full_text": detail.full_text[:10000],
            "referenced_sections": detail.referenced_sections,
            "document_references": detail.document_references,
            "identified_flaws": detail.identified_flaws,
            "scraped_at": detail.scraped_at,
        }
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        with open(self.progress_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "case_id": detail.metadata.case_id,
                "scraped_at": detail.scraped_at,
            }, ensure_ascii=False) + "\n")

        self.scraped_ids.add(detail.metadata.case_id)

    def close(self):
        self.client.close()


# ─── Shared Extraction Functions ──────────────────────────────────

def _extract_bgb_sections(text: str) -> list[str]:
    """Extract BGB section references from decision text."""
    patterns = [
        r"§\s*(\d+[a-z]?)\s*(?:Abs\.\s*\d+\s*)?(?:S\.\s*\d+\s*)?(?:Nr\.\s*\d+\s*)?BGB",
        r"§§\s*([\d,\s]+(?:bis|[-–])\s*\d+[a-z]?)\s*BGB",
        r"BGB\s*§\s*(\d+[a-z]?)",
    ]
    sections = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            sections.add(f"§{match.group(1)} BGB")
    return sorted(sections)


def _extract_de_document_refs(text: str) -> list[str]:
    """
    Extract references to real-world documents from German court decisions.

    These document types appear in real disputes — the goldmine for
    understanding what documents exist and what goes wrong with them.
    """
    doc_patterns = [
        # Lease and rental
        r"Mietvertrag(?:es?|s)?",
        r"Untermietvertrag",
        r"Gewerbemietvertrag",
        r"Staffelmietvertrag",
        r"Indexmietvertrag",
        # Cost statements
        r"Nebenkostenabrechnung(?:en)?",
        r"Betriebskostenabrechnung(?:en)?",
        r"Heizkostenabrechnung(?:en)?",
        r"Hausgeldabrechnung(?:en)?",
        r"Jahresabrechnung(?:en)?",
        # Notices and letters
        r"Kündigungsschreiben",
        r"Mieterhöhungsverlangen",
        r"Mängelanzeige",
        r"Abmahnung",
        r"Räumungsaufforderung",
        # Protocols and reports
        r"Übergabeprotokoll(?:s|e)?",
        r"Wohnungsübergabeprotokoll",
        r"Zustandsbericht",
        r"Gutachten",
        r"Sachverständigengutachten",
        # Purchase and property
        r"Kaufvertrag(?:es?|s)?",
        r"Grundbuchauszug",
        r"Teilungserklärung",
        r"Gemeinschaftsordnung",
        r"Hausordnung",
        # Construction
        r"Bauvertrag(?:es?|s)?",
        r"Werkvertrag(?:es?|s)?",
        r"Bauabnahmeprotokoll",
        r"Leistungsverzeichnis",
        r"Baubeschreibung",
        # Insurance
        r"Versicherungspolice",
        r"Wohngebäudeversicherung",
        r"Hausratversicherung",
        # Financial
        r"Mietschuldenfreiheitsbescheinigung",
        r"Schufa-Auskunft",
        r"Einkommensnachweis",
        r"Bürgschaftserklärung",
        r"Mietbürgschaft",
    ]

    refs = set()
    for pattern in doc_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            match = re.search(pattern, text, re.IGNORECASE)
            refs.add(match.group())
    return sorted(refs)


def _extract_de_flaws(text: str) -> list[str]:
    """
    Extract mentions of document flaws from German court decisions.

    These are the actual error patterns that courts identify —
    the basis for our domain-aware error injection system.
    """
    flaw_patterns = [
        # Formal defects
        (r"formell(?:e|er|es)?\s+(?:un)?wirksam", "formal_validity"),
        (r"Formfehler", "formal_error"),
        (r"formnichtig", "form_void"),
        (r"Schriftform(?:erfordernis)?(?:\s+nicht\s+(?:eingehalten|gewahrt))?", "written_form"),
        # Calculation errors
        (r"Berechnungsfehler", "calculation_error"),
        (r"rechnerisch(?:e|er)?\s+(?:un)?richtig", "arithmetic_error"),
        (r"falsch(?:e|er)?\s+(?:Berechnung|berechnet)", "wrong_calculation"),
        (r"Rechenfehler", "arithmetic_mistake"),
        # Missing information
        (r"fehlende(?:r|s|n)?\s+Angabe", "missing_information"),
        (r"unvollständig(?:e|er|es)?", "incomplete"),
        (r"lückenhaft", "gaps"),
        (r"nicht\s+(?:angegeben|mitgeteilt|aufgeführt)", "not_stated"),
        # Incorrect information
        (r"unrichtig(?:e|er|es)?\s+Angabe", "incorrect_information"),
        (r"fehlerhaft(?:e|er|es)?", "erroneous"),
        (r"irrtümlich", "mistaken"),
        (r"falsch(?:e|er|es)?\s+(?:Angabe|Bezeichnung)", "false_statement"),
        # Deadline violations
        (r"Frist(?:\s+nicht\s+(?:eingehalten|gewahrt))?(?:versäumnis)?", "deadline_violation"),
        (r"verspätet(?:e|er|es)?", "late"),
        (r"verfristet", "time_barred"),
        # Signature/authentication
        (r"Unterschrift\s+fehlt", "missing_signature"),
        (r"nicht\s+(?:unter)?zeichnet", "unsigned"),
        # Contradictions
        (r"widersprüchlich(?:e|er|es)?", "contradictory"),
        (r"Widerspruch", "contradiction"),
        (r"widerspricht", "contradicts"),
        # Clarity issues
        (r"unklar(?:e|er|es)?", "unclear"),
        (r"mehrdeutig", "ambiguous"),
        (r"intransparent", "non_transparent"),
        (r"Transparenz(?:gebot|kontrolle)?", "transparency_requirement"),
        # Unfair terms (AGB)
        (r"überraschende\s+Klausel", "surprising_clause"),
        (r"unangemessene\s+Benachteiligung", "unfair_disadvantage"),
        (r"AGB-(?:Kontrolle|widrig|rechtswidrig)", "agb_control"),
        (r"unwirksame?\s+Klausel", "void_clause"),
    ]

    flaws = []
    for pattern, flaw_type in flaw_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].replace("\n", " ")
            flaws.append({
                "type": flaw_type,
                "match": match.group(),
                "context": context,
            })

    return flaws


# ─── Unified Bulk Scraper ────────────────────────────────────────

class GermanyCourtScraper:
    """
    Unified scraper that combines all German sources.

    Priority order:
    1. Open Legal Data (API — cleanest data)
    2. dejure.org (BGB section references)
    3. OpenJur (broad keyword search)
    """

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.oldp = OLDPScraper(output_dir)
        self.dejure = DeJureScraper(output_dir)
        self.openjur = OpenJurScraper(output_dir)

    def bulk_scrape(self, max_per_query: int = 30):
        """Run all predefined queries across all sources."""
        total_scraped = 0
        total_flaws = 0
        total_doc_refs = 0

        # Phase 1: Open Legal Data API
        logger.info("\n" + "="*60)
        logger.info("PHASE 1: Open Legal Data API")
        logger.info("="*60)

        for query_def in MIETRECHT_QUERIES:
            keyword = query_def["keyword"]
            category = query_def["category"]
            logger.info(f"\nQuery: '{keyword}' (category: {category})")

            results = self.oldp.search(keyword, max_results=max_per_query)
            logger.info(f"  Found {len(results)} results")

            for i, case_data in enumerate(results):
                detail = self.oldp.process_case(case_data, category=category, query=keyword)
                if detail:
                    self._save_unified(detail, "oldp")
                    total_scraped += 1
                    total_flaws += len(detail.identified_flaws)
                    total_doc_refs += len(detail.document_references)

        # Phase 2: dejure.org BGB section traversal
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: dejure.org — Mietrecht BGB sections")
        logger.info("="*60)

        for section in MIETRECHT_SECTIONS:
            cases = self.dejure.get_cases_for_section(section, max_cases=10)
            for case_meta in cases:
                detail = self.dejure.get_case_detail(case_meta)
                if detail and detail.full_text:
                    self.dejure._save(detail)
                    total_scraped += 1
                    total_flaws += len(detail.identified_flaws)
                    total_doc_refs += len(detail.document_references)

        # Phase 3: OpenJur keyword search
        logger.info("\n" + "="*60)
        logger.info("PHASE 3: OpenJur — Keyword search")
        logger.info("="*60)

        for query_def in MIETRECHT_QUERIES[:10]:  # Top 10 queries only
            keyword = query_def["keyword"]
            category = query_def["category"]

            cases = self.openjur.search(keyword, max_results=max_per_query)
            for case_meta in cases:
                case_meta.category = category
                detail = self.openjur.get_case_detail(case_meta)
                if detail and detail.full_text:
                    self.openjur._save(detail)
                    total_scraped += 1
                    total_flaws += len(detail.identified_flaws)
                    total_doc_refs += len(detail.document_references)

        logger.info(f"\n{'='*60}")
        logger.info(f"BULK SCRAPE COMPLETE")
        logger.info(f"  Cases scraped: {total_scraped}")
        logger.info(f"  Total flaws found: {total_flaws}")
        logger.info(f"  Total document references: {total_doc_refs}")
        logger.info(f"{'='*60}")

    def _save_unified(self, detail: DECaseDetail, source: str):
        """Save to unified output file."""
        out_file = self.output_dir / f"{source}_{detail.metadata.category}.jsonl"
        record = {
            "metadata": asdict(detail.metadata),
            "full_text": detail.full_text[:10000],
            "tenor": detail.tenor[:2000],
            "tatbestand": detail.tatbestand[:3000],
            "gruende": detail.gruende[:3000],
            "leitsatz": detail.leitsatz[:1000],
            "referenced_sections": detail.referenced_sections,
            "document_references": detail.document_references,
            "identified_flaws": detail.identified_flaws,
            "scraped_at": detail.scraped_at,
        }
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def generate_flaw_taxonomy(self):
        """Analyze all scraped data and produce a flaw taxonomy."""
        flaw_counts: dict[str, int] = {}
        flaw_examples: dict[str, list[str]] = {}
        doc_ref_counts: dict[str, int] = {}

        for jsonl_file in self.output_dir.glob("*.jsonl"):
            if jsonl_file.name.startswith("."):
                continue
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    for flaw in record.get("identified_flaws", []):
                        ft = flaw["type"]
                        flaw_counts[ft] = flaw_counts.get(ft, 0) + 1
                        if ft not in flaw_examples:
                            flaw_examples[ft] = []
                        if len(flaw_examples[ft]) < 5:
                            flaw_examples[ft].append(flaw.get("context", ""))

                    for ref in record.get("document_references", []):
                        doc_ref_counts[ref] = doc_ref_counts.get(ref, 0) + 1

        report = {
            "generated_at": datetime.now().isoformat(),
            "country": "Germany",
            "flaw_taxonomy": {
                ft: {"count": c, "examples": flaw_examples.get(ft, [])}
                for ft, c in sorted(flaw_counts.items(), key=lambda x: -x[1])
            },
            "document_types_referenced": {
                ref: count
                for ref, count in sorted(doc_ref_counts.items(), key=lambda x: -x[1])
            },
        }

        report_path = self.output_dir / "flaw_taxonomy.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Taxonomy written to: {report_path}")
        return report

    def close(self):
        self.oldp.close()
        self.dejure.close()
        self.openjur.close()


# ─── CLI ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="German Court Decision Scraper for Mietrecht"
    )
    parser.add_argument(
        "--source", choices=["oldp", "dejure", "openjur", "all"],
        default="all",
        help="Data source (default: all)",
    )
    parser.add_argument("--search", type=str, help="Search keyword")
    parser.add_argument("--section", type=int, help="BGB section number (for dejure)")
    parser.add_argument("--max", type=int, default=50, help="Max results per query")
    parser.add_argument("--bulk", action="store_true", help="Run all predefined queries")
    parser.add_argument("--taxonomy", action="store_true", help="Generate flaw taxonomy")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="Output directory")

    args = parser.parse_args()

    scraper = GermanyCourtScraper(output_dir=args.output)

    try:
        if args.taxonomy:
            scraper.generate_flaw_taxonomy()
        elif args.bulk:
            scraper.bulk_scrape(max_per_query=args.max)
            scraper.generate_flaw_taxonomy()
        elif args.search:
            if args.source in ("oldp", "all"):
                results = scraper.oldp.search(args.search, max_results=args.max)
                for r in results:
                    detail = scraper.oldp.process_case(r, query=args.search)
                    if detail:
                        scraper._save_unified(detail, "oldp")
            if args.source in ("openjur", "all"):
                cases = scraper.openjur.search(args.search, max_results=args.max)
                for c in cases:
                    detail = scraper.openjur.get_case_detail(c)
                    if detail:
                        scraper.openjur._save(detail)
        elif args.section:
            cases = scraper.dejure.get_cases_for_section(args.section, max_cases=args.max)
            for c in cases:
                detail = scraper.dejure.get_case_detail(c)
                if detail:
                    scraper.dejure._save(detail)
        else:
            parser.print_help()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
