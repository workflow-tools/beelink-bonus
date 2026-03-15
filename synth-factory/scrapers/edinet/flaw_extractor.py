"""
Financial report flaw taxonomy extractor.

Analyzes parsed EDINET securities reports to identify common patterns of
errors, omissions, and structural issues. These patterns are then used by
the synth-factory's error injection system to generate "eerily real"
synthetic documents with domain-authentic flaws.

Flaw categories for 有価証券報告書:
1. STRUCTURAL — missing sections, out-of-order sections, truncated content
2. NUMERICAL — inconsistent figures, rounding errors, stale data
3. DISCLOSURE — vague risk factors, boilerplate language, missing specifics
4. FORMATTING — encoding artifacts, garbled tables, broken references
5. REGULATORY — non-compliance with recent disclosure requirements
6. TEMPORAL — outdated policies, stale comparisons, wrong fiscal year refs

The extractor builds a flaw_taxonomy.json that the YAML config references
for error injection. This is the key differentiator: we don't inject random
noise, we inject the exact types of errors that show up in real filings.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from ..base.base_scraper import DocumentRecord

logger = logging.getLogger(__name__)


# ─── Flaw Taxonomy Types ───────────────────────────────────────


@dataclass
class FlawInstance:
    """A single observed flaw in a specific document."""
    flaw_type: str                     # Top-level category
    flaw_subtype: str                  # Specific sub-category
    segment: str                       # Which document segment
    description: str                   # Human-readable description
    source_id: str = ""                # Document where observed
    severity: str = "medium"           # low, medium, high
    example_text: str = ""             # Snippet showing the flaw
    confidence: float = 0.8            # How confident in the detection


@dataclass
class FlawCategory:
    """A category of flaws with frequency data."""
    flaw_type: str
    flaw_subtype: str
    description: str
    segment: str = ""
    count: int = 0
    frequency: float = 0.0            # Proportion of documents with this flaw
    severity: str = "medium"
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FlawTaxonomy:
    """
    Complete flaw taxonomy for a document type.

    This is the output of the extractor and the input to the
    synth-factory's error injection system.
    """
    source_name: str = "edinet"
    document_type: str = "securities_report_jp"
    total_documents_analyzed: int = 0
    categories: list[FlawCategory] = field(default_factory=list)
    last_updated: str = ""

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "document_type": self.document_type,
            "total_documents_analyzed": self.total_documents_analyzed,
            "last_updated": self.last_updated,
            "categories": [c.to_dict() for c in self.categories],
        }

    def save(self, path: Path) -> None:
        """Save taxonomy to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"Saved flaw taxonomy to {path} ({len(self.categories)} categories)")

    @classmethod
    def load(cls, path: Path) -> "FlawTaxonomy":
        """Load taxonomy from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        taxonomy = cls(
            source_name=data["source_name"],
            document_type=data["document_type"],
            total_documents_analyzed=data["total_documents_analyzed"],
            last_updated=data.get("last_updated", ""),
        )
        for cat_data in data.get("categories", []):
            taxonomy.categories.append(FlawCategory(**cat_data))
        return taxonomy


# ─── Detection Patterns ────────────────────────────────────────


# Each pattern: (compiled_regex, flaw_type, flaw_subtype, segment, severity, description)
FLAW_PATTERNS = [
    # ── STRUCTURAL ──
    (
        re.compile(r'(?:該当事項は|該当なし|記載すべき事項は)(?:ありません|なし)', re.IGNORECASE),
        "structural", "empty_section", "", "low",
        "Section marked as empty/not applicable (may be legitimate or evasive)",
    ),
    (
        re.compile(r'(?:前事業年度|前連結会計年度).*?と同様', re.DOTALL),
        "structural", "stale_reference", "", "medium",
        "Content references previous period without updated details",
    ),

    # ── NUMERICAL ──
    (
        re.compile(r'(\d{1,3}(?:,\d{3})*)\s*(?:百万円|千円).*?\1\s*(?:百万円|千円)', re.DOTALL),
        "numerical", "potential_duplicate_figure", "financial_statements", "medium",
        "Same numerical figure appears multiple times (potential copy-paste)",
    ),
    (
        re.compile(r'(?:△|▲)\s*[\d,]+\s*(?:百万円|千円)', re.IGNORECASE),
        "numerical", "negative_indicator", "financial_statements", "low",
        "Negative number indicator (normal but important for accuracy)",
    ),

    # ── DISCLOSURE ──
    (
        re.compile(r'(?:一般的に|通常|一般論として|概して)', re.IGNORECASE),
        "disclosure", "generic_language", "business_risks", "medium",
        "Generic/vague language in disclosure (may lack specificity)",
    ),
    (
        re.compile(
            r'(?:為替|金利|原油|原材料|自然災害|感染症|パンデミック|地政学)'
            r'.*?(?:リスク|影響|変動)',
            re.DOTALL,
        ),
        "disclosure", "boilerplate_risk", "business_risks", "low",
        "Common boilerplate risk factor (check if company-specific details added)",
    ),
    (
        re.compile(r'(?:重要な|特筆すべき).*?(?:ありません|なし|認められません)'),
        "disclosure", "negative_assurance", "", "low",
        "Negative assurance statement (common but may obscure issues)",
    ),

    # ── FORMATTING ──
    (
        re.compile(r'[□■◆◇▲△▽▼●○★☆]{2,}'),
        "formatting", "garbled_symbols", "", "high",
        "Multiple consecutive special symbols (likely encoding/OCR artifact)",
    ),
    (
        re.compile(r'[\x00-\x08\x0e-\x1f]'),
        "formatting", "control_characters", "", "high",
        "Control characters in text (encoding error)",
    ),
    (
        re.compile(r'(?:â€|ã€|Ã¤|Ã¶|Ã¼|â€™|â€œ)'),
        "formatting", "mojibake", "", "high",
        "UTF-8 mojibake (incorrect encoding/decoding)",
    ),

    # ── REGULATORY ──
    (
        re.compile(r'(?:サステナビリティ|ESG|気候変動|TCFD)', re.IGNORECASE),
        "regulatory", "sustainability_disclosure", "business_status", "low",
        "Sustainability/ESG disclosure (increasingly required by FSA)",
    ),
    (
        re.compile(
            r'(?:人的資本|人材育成|ダイバーシティ|多様性)',
            re.IGNORECASE,
        ),
        "regulatory", "human_capital_disclosure", "business_status", "low",
        "Human capital disclosure (required since 2023 amendments)",
    ),

    # ── TEMPORAL ──
    (
        re.compile(r'(?:令和\d+年|20\d{2}年)\d{1,2}月\d{1,2}日現在'),
        "temporal", "reference_date", "", "low",
        "Date reference point (check if current)",
    ),
]


# ─── Extractor ──────────────────────────────────────────────────


class FlawExtractor:
    """
    Analyze parsed documents to build a flaw taxonomy.

    Usage:
        extractor = FlawExtractor()
        for record in parsed_records:
            extractor.analyze(record)
        taxonomy = extractor.build_taxonomy()
        taxonomy.save(Path("output/flaw_taxonomy.json"))
    """

    def __init__(self):
        self._instances: list[FlawInstance] = []
        self._documents_analyzed: int = 0
        self._segment_lengths: dict[str, list[int]] = defaultdict(list)

    def analyze(self, record: DocumentRecord) -> list[FlawInstance]:
        """
        Analyze a single parsed document for flaws.

        Returns list of detected FlawInstances.
        """
        self._documents_analyzed += 1
        instances = []

        # Analyze each segment
        for seg_name, seg_text in record.segments.items():
            self._segment_lengths[seg_name].append(len(seg_text))

            # Run pattern-based detection
            for pattern, flaw_type, subtype, target_seg, severity, desc in FLAW_PATTERNS:
                # If pattern targets a specific segment, only check that one
                if target_seg and target_seg != seg_name:
                    continue

                matches = pattern.findall(seg_text)
                if matches:
                    example = matches[0] if isinstance(matches[0], str) else str(matches[0])
                    instance = FlawInstance(
                        flaw_type=flaw_type,
                        flaw_subtype=subtype,
                        segment=seg_name,
                        description=desc,
                        source_id=record.source_id,
                        severity=severity,
                        example_text=example[:200],
                    )
                    instances.append(instance)

            # Structural: check for unusually short sections
            if len(seg_text) < 100:
                instances.append(FlawInstance(
                    flaw_type="structural",
                    flaw_subtype="suspiciously_short",
                    segment=seg_name,
                    description=f"Section '{seg_name}' is unusually short ({len(seg_text)} chars)",
                    source_id=record.source_id,
                    severity="medium",
                ))

        # Structural: check for missing expected segments
        expected = {
            "company_overview", "business_status", "md_and_a",
            "business_risks", "financial_statements",
        }
        missing = expected - set(record.segments.keys())
        for seg in missing:
            instances.append(FlawInstance(
                flaw_type="structural",
                flaw_subtype="missing_section",
                segment=seg,
                description=f"Expected section '{seg}' not found in document",
                source_id=record.source_id,
                severity="high",
            ))

        self._instances.extend(instances)
        return instances

    def build_taxonomy(self) -> FlawTaxonomy:
        """
        Aggregate all detected flaws into a taxonomy with frequency data.

        Returns a FlawTaxonomy suitable for driving error injection.
        """
        from datetime import datetime, timezone

        # Group by (type, subtype, segment)
        counter: Counter = Counter()
        examples_by_key: dict[tuple, list[str]] = defaultdict(list)
        severity_by_key: dict[tuple, str] = {}
        desc_by_key: dict[tuple, str] = {}

        for inst in self._instances:
            key = (inst.flaw_type, inst.flaw_subtype, inst.segment)
            counter[key] += 1
            severity_by_key[key] = inst.severity
            desc_by_key[key] = inst.description
            if inst.example_text and len(examples_by_key[key]) < 3:
                examples_by_key[key].append(inst.example_text)

        total = max(self._documents_analyzed, 1)
        categories = []
        for (ftype, subtype, segment), count in counter.most_common():
            categories.append(FlawCategory(
                flaw_type=ftype,
                flaw_subtype=subtype,
                description=desc_by_key[(ftype, subtype, segment)],
                segment=segment,
                count=count,
                frequency=round(count / total, 4),
                severity=severity_by_key[(ftype, subtype, segment)],
                examples=examples_by_key[(ftype, subtype, segment)],
            ))

        taxonomy = FlawTaxonomy(
            source_name="edinet",
            document_type="securities_report_jp",
            total_documents_analyzed=self._documents_analyzed,
            categories=categories,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"Built flaw taxonomy: {len(categories)} categories "
            f"from {self._documents_analyzed} documents"
        )
        return taxonomy

    def reset(self) -> None:
        """Clear accumulated analysis data."""
        self._instances.clear()
        self._documents_analyzed = 0
        self._segment_lengths.clear()
