"""
EDINET API v2 client — low-level HTTP interface to Japan's FSA disclosure system.

Endpoints:
  GET /api/v2/documents.json   — list filings by date
  GET /api/v2/documents/{docID} — download filing content (ZIP)

Authentication: Subscription-Key query parameter (free, requires registration)
Rate limit: conservative 1 req/sec default (official limit undocumented)

This module handles ONLY the HTTP layer. Parsing is in edinet_parser.py.
"""

from __future__ import annotations

import io
import json
import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..base.base_scraper import HttpClient, HttpResponse, RealHttpClient

logger = logging.getLogger(__name__)


# ─── Configuration ──────────────────────────────────────────────


@dataclass
class EdinetConfig:
    """EDINET API connection settings."""
    api_key: str = ""                  # Subscription-Key
    base_url: str = "https://api.edinet-fsa.go.jp/api/v2"
    timeout: float = 60.0
    # Document type filters
    # 120 = 有価証券報告書 (Annual Securities Report)
    # 140 = 四半期報告書 (Quarterly Report)
    # 160 = 半期報告書 (Semi-Annual Report)
    target_doc_types: list[str] = field(
        default_factory=lambda: ["120"]
    )
    # Download type: 1=XBRL+PDF, 2=PDF only, 3=attachments, 4=English
    download_type: int = 1


# ─── Response Models ────────────────────────────────────────────


@dataclass
class EdinetDocumentInfo:
    """Single document from the EDINET listing endpoint."""
    doc_id: str
    edinet_code: str
    filer_name: str
    doc_type_code: str
    doc_description: str
    filing_date: str
    submit_date_time: str = ""
    ordinance_code: str = ""
    form_code: str = ""
    period_start: str = ""
    period_end: str = ""
    withdrawal_status: str = "0"
    doc_info_edit_status: str = "0"
    disclosure_status: str = "0"
    # Raw extra fields from API
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_dict(cls, d: dict) -> "EdinetDocumentInfo":
        """Parse from EDINET API response dict."""
        known_fields = {
            "docID": "doc_id",
            "edinetCode": "edinet_code",
            "filerName": "filer_name",
            "docTypeCode": "doc_type_code",
            "docDescription": "doc_description",
            "filingDate": "filing_date",
            "submitDateTime": "submit_date_time",
            "ordinanceCode": "ordinance_code",
            "formCode": "form_code",
            "periodStart": "period_start",
            "periodEnd": "period_end",
            "withdrawalStatus": "withdrawal_status",
            "docInfoEditStatus": "doc_info_edit_status",
            "disclosureStatus": "disclosure_status",
        }
        kwargs = {}
        extra = {}
        for api_key, value in d.items():
            if api_key in known_fields:
                kwargs[known_fields[api_key]] = str(value) if value is not None else ""
            else:
                extra[api_key] = value
        kwargs["extra"] = extra
        return cls(**kwargs)

    @property
    def is_withdrawn(self) -> bool:
        return self.withdrawal_status not in ("0", "")

    @property
    def doc_type_label(self) -> str:
        """Human-readable document type."""
        labels = {
            "120": "有価証券報告書",
            "130": "有価証券報告書（訂正）",
            "140": "四半期報告書",
            "150": "四半期報告書（訂正）",
            "160": "半期報告書",
            "170": "半期報告書（訂正）",
            "180": "臨時報告書",
            "350": "大量保有報告書",
        }
        return labels.get(self.doc_type_code, f"Type-{self.doc_type_code}")


# ─── Client ─────────────────────────────────────────────────────


class EdinetClient:
    """
    Low-level EDINET API v2 client.

    Handles:
    - Document listing by date with type filtering
    - Document ZIP download + extraction
    - Error handling and response validation
    """

    def __init__(
        self,
        config: EdinetConfig | None = None,
        http_client: HttpClient | None = None,
    ):
        self.config = config or EdinetConfig()
        self.http = http_client or RealHttpClient()

    def list_documents_by_date(self, date: str) -> list[EdinetDocumentInfo]:
        """
        List all filings submitted on a given date.

        Args:
            date: Date string in YYYY-MM-DD format.

        Returns:
            List of EdinetDocumentInfo, filtered by target_doc_types.
        """
        url = f"{self.config.base_url}/documents.json"
        params = {
            "date": date,
            "type": 2,  # 2 = include full document information
        }
        if self.config.api_key:
            params["Subscription-Key"] = self.config.api_key

        response = self.http.get(url, params=params, timeout=self.config.timeout)
        response.raise_for_status()

        data = response.json()

        # Validate response structure
        metadata = data.get("metadata", {})
        status = metadata.get("status")
        if status and str(status) != "200":
            error_msg = metadata.get("message", "Unknown EDINET error")
            raise EdinetApiError(f"EDINET API error: {error_msg} (status={status})")

        results = data.get("results", [])
        if results is None:
            return []

        # Parse and filter
        documents = []
        for item in results:
            try:
                doc = EdinetDocumentInfo.from_api_dict(item)
                # Filter by target document types
                if doc.doc_type_code in self.config.target_doc_types:
                    # Skip withdrawn documents
                    if not doc.is_withdrawn:
                        documents.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse EDINET document: {e}")
                continue

        logger.debug(
            f"EDINET {date}: {len(results)} total filings, "
            f"{len(documents)} matching target types "
            f"{self.config.target_doc_types}"
        )
        return documents

    def download_document(
        self,
        doc_id: str,
        output_dir: Path | None = None,
        download_type: int | None = None,
    ) -> dict[str, bytes]:
        """
        Download a filing as ZIP and extract its contents.

        Args:
            doc_id: EDINET document ID.
            output_dir: If provided, save extracted files here.
            download_type: Override default download type (1=XBRL+PDF, etc.)

        Returns:
            Dict of {filename: content_bytes} from the extracted ZIP.
        """
        dtype = download_type or self.config.download_type
        url = f"{self.config.base_url}/documents/{doc_id}"
        params = {"type": dtype}
        if self.config.api_key:
            params["Subscription-Key"] = self.config.api_key

        response = self.http.get(url, params=params, timeout=self.config.timeout)
        response.raise_for_status()

        # Check if response is actually a ZIP
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            # Error response returned as JSON instead of ZIP
            try:
                error_data = json.loads(response.content)
                msg = error_data.get("metadata", {}).get("message", "Unknown error")
                raise EdinetApiError(f"EDINET download error for {doc_id}: {msg}")
            except json.JSONDecodeError:
                raise EdinetApiError(
                    f"EDINET unexpected response for {doc_id}: "
                    f"content-type={content_type}"
                )

        # Extract ZIP
        try:
            zip_buffer = io.BytesIO(response.content)
            extracted = {}
            with zipfile.ZipFile(zip_buffer, "r") as zf:
                for name in zf.namelist():
                    extracted[name] = zf.read(name)

                    # Optionally save to disk
                    if output_dir:
                        out_path = output_dir / doc_id / name
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        out_path.write_bytes(extracted[name])

            logger.debug(
                f"Downloaded {doc_id}: {len(extracted)} files, "
                f"total {sum(len(v) for v in extracted.values())} bytes"
            )
            return extracted

        except zipfile.BadZipFile:
            raise EdinetApiError(
                f"EDINET returned invalid ZIP for {doc_id} "
                f"({len(response.content)} bytes)"
            )

    def get_document_types(self) -> dict[str, str]:
        """Return known EDINET document type codes and labels."""
        return {
            "120": "有価証券報告書 (Annual Securities Report)",
            "130": "有価証券報告書（訂正） (Amended Annual Report)",
            "140": "四半期報告書 (Quarterly Report)",
            "150": "四半期報告書（訂正） (Amended Quarterly Report)",
            "160": "半期報告書 (Semi-Annual Report)",
            "170": "半期報告書（訂正） (Amended Semi-Annual Report)",
            "180": "臨時報告書 (Extraordinary Report)",
            "190": "臨時報告書（訂正） (Amended Extraordinary Report)",
            "350": "大量保有報告書 (Large Shareholding Report)",
        }


class EdinetApiError(Exception):
    """Raised when the EDINET API returns an error."""
    pass
