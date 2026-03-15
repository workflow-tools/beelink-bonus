"""
Dataset configuration schema using Pydantic.

Each dataset is defined by a YAML config file that specifies:
- Metadata (name, version, description, license)
- Table schemas (columns with types, distributions, constraints)
- Document type definitions (segment-based long-text generation blueprints)
- Generation settings (method, epochs, batch size)
- LLM augmentation settings (which columns, which model, prompts)
- Validation settings (which tests to run)

The config is the single source of truth for reproducible generation.

Supports two generation modes:
1. Tabular: SDV-based rows with short LLM-augmented text columns (existing)
2. Document: Segment-based long-text generation with context threading (new)
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, Field


class ColumnType(str, Enum):
    """Supported column data types."""
    TEXT = "text"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    ID = "id"


class TextGenerator(str, Enum):
    """How to generate text columns."""
    FAKER = "faker"           # Faker library (fast, rule-based)
    OLLAMA = "ollama"         # LLM-generated via Ollama (slow, high quality)
    TEMPLATE = "template"     # Python f-string templates
    WEIGHTED_SAMPLE = "weighted_sample"  # Sample from a reference file


class Distribution(str, Enum):
    """Statistical distributions for numeric columns."""
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"
    EXPONENTIAL = "exponential"
    POISSON = "poisson"
    BETA = "beta"


class GenerationMethod(str, Enum):
    """SDV synthesizer to use for tabular generation."""
    CTGAN = "ctgan"
    COPULA = "copula"
    GAUSSIAN_COPULA = "gaussian_copula"
    TVAE = "tvae"


class LicenseType(str, Enum):
    """Dataset license options."""
    CC_BY_4 = "CC-BY-4.0"
    CC_BY_SA_4 = "CC-BY-SA-4.0"
    CC_BY_NC_4 = "CC-BY-NC-4.0"
    COMMERCIAL = "commercial"
    CUSTOM = "custom"


# ─── Column Definitions ───────────────────────────────────────────

class DistributionParams(BaseModel):
    """Parameters for statistical distributions."""
    mean: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = Field(None, alias="min")
    max_val: Optional[float] = Field(None, alias="max")
    shape: Optional[float] = None
    rate: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None

    model_config = {"populate_by_name": True}


class OllamaConfig(BaseModel):
    """Configuration for LLM-generated text columns."""
    model: str = "llama3.1:70b-instruct-q4_K_M"
    prompt: str
    temperature: float = 0.8
    max_tokens: int = 100
    system_prompt: Optional[str] = None
    # Variables in the prompt that reference other columns, e.g., {branche}
    context_columns: list[str] = Field(default_factory=list)


class FakerConfig(BaseModel):
    """Configuration for Faker-generated columns."""
    provider: str  # e.g., "company", "address", "name"
    locale: str = "de_DE"
    kwargs: dict = Field(default_factory=dict)


class ColumnDef(BaseModel):
    """Definition of a single column in a table."""
    name: str
    type: ColumnType
    description: Optional[str] = None

    # For categorical columns
    values: Optional[list[str]] = None
    weights: Optional[list[float]] = None

    # For numeric columns
    distribution: Optional[Distribution] = None
    dist_params: Optional[DistributionParams] = None
    decimals: Optional[int] = None

    # For text columns
    generator: Optional[TextGenerator] = None
    ollama: Optional[OllamaConfig] = None
    faker: Optional[FakerConfig] = None
    template: Optional[str] = None  # Python f-string, e.g., "{firma_name} {rechtsform}"

    # For weighted_sample generator
    sample_source: Optional[str] = None  # path to CSV file in seeds/

    # For datetime columns
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None

    # For ID columns
    prefix: Optional[str] = None  # e.g., "INV-" for invoice IDs
    sequential: bool = False

    # Constraints
    nullable: bool = False
    null_ratio: float = 0.0  # fraction of nulls if nullable
    unique: bool = False


# ─── Document Segment Definitions ─────────────────────────────────

class SegmentType(str, Enum):
    """Types of document segments."""
    SECTION = "section"          # Prose narrative paragraph(s)
    FORM_FIELD = "form_field"    # Labeled structured field
    LIST_FIELD = "list_field"    # Repeated items (e.g., 3 prior addresses)


class SegmentDef(BaseModel):
    """
    Definition of a single segment within a document type.

    Each segment gets its own LLM call with context from prior segments.
    This enables coherent multi-section document generation without
    requiring a single enormous prompt.
    """
    name: str                    # e.g., "personal_details", "findings"
    segment_type: SegmentType
    description: Optional[str] = None

    # Display label rendered in the assembled document
    label: Optional[str] = None  # e.g., "1. 個人情報" or "Zusammenfassung"

    # LLM generation settings
    prompt: str                  # Template with {variable} placeholders
    system_prompt: Optional[str] = None
    model: Optional[str] = None  # Override default model for this segment
    temperature: float = 0.8
    max_tokens: int = 500

    # Context threading: names of prior segments whose output
    # is injected into this segment's prompt via {segment_name}
    context_dependencies: list[str] = Field(default_factory=list)

    # For LIST_FIELD segments: how many items to generate
    list_min: Optional[int] = None
    list_max: Optional[int] = None

    # Validation constraints for this segment
    min_length: Optional[int] = None   # Minimum characters
    max_length: Optional[int] = None   # Maximum characters
    required_keywords: Optional[list[str]] = None  # Must contain these strings


class DocumentTypeDef(BaseModel):
    """
    Blueprint for a document type.

    Defines the ordered sequence of segments that compose a document.
    Adding a new document type = writing a new YAML config with a new
    DocumentTypeDef. No code changes required.
    """
    name: str                    # e.g., "housing_application_jp"
    description: Optional[str] = None
    language: str = "ja"         # ISO language code

    # Ordered segments — generated top-to-bottom with context threading
    segments: list[SegmentDef]

    # Optional front matter rendered before segments
    preamble: Optional[str] = None  # Template, e.g., "# 住宅管理申請書\n{document_id}"

    # Output format for assembled document
    format: str = "markdown"     # "markdown", "json", "plain"

    # Optional: inject realistic errors into a fraction of documents
    error_injection_rate: float = 0.0  # 0.05 = 5% of docs get realistic errors

    # Path to a flaw_taxonomy.json built by the FlawExtractor.
    # When set + use_taxonomy_errors=True, the error injector selects
    # flaw types weighted by real-world frequency instead of uniform random.
    flaw_taxonomy_path: Optional[str] = None
    use_taxonomy_errors: bool = False


class DocumentTableDef(BaseModel):
    """
    A table that contains document data (not tabular rows).

    Each record in this table is one complete document assembled
    from segments defined by the referenced DocumentTypeDef.
    """
    name: str
    description: Optional[str] = None
    records: int
    document_type: str           # References DocumentTypeDef.name

    # Optional: inherit context from a tabular table's columns
    # e.g., pull applicant_name, birth_date from a "people" table
    seed_table: Optional[str] = None
    seed_columns: list[str] = Field(default_factory=list)


# ─── Table Definitions ─────────────────────────────────────────────

class ForeignKey(BaseModel):
    """Foreign key relationship between tables."""
    column: str
    references_table: str
    references_column: str


class TableDef(BaseModel):
    """Definition of a single table in the dataset."""
    name: str
    description: Optional[str] = None
    records: int
    columns: list[ColumnDef]
    foreign_keys: list[ForeignKey] = Field(default_factory=list)
    # If provided, fit the model to this seed CSV instead of using distributions
    seed_file: Optional[str] = None


# ─── Generation Settings ──────────────────────────────────────────

class GenerationSettings(BaseModel):
    """Configuration for the SDV generation step."""
    method: GenerationMethod = GenerationMethod.GAUSSIAN_COPULA
    epochs: int = 300
    batch_size: int = 500
    # Ollama concurrency for text augmentation
    ollama_concurrent: int = 2
    ollama_base_url: str = "http://localhost:11434"
    # Default model for text augmentation (can be overridden per column)
    ollama_default_model: str = "llama3.1:70b-instruct-q4_K_M"


# ─── Validation Settings ──────────────────────────────────────────

class ValidationSettings(BaseModel):
    """Configuration for the Evidently validation step."""
    enabled: bool = True
    # Evidently test presets to run
    test_presets: list[str] = Field(
        default_factory=lambda: ["data_quality", "data_drift"]
    )
    # Custom validation checks (Python callables registered in validators/)
    custom_checks: list[str] = Field(default_factory=list)
    # Minimum quality score to pass (0.0-1.0)
    min_quality_score: float = 0.7
    # Generate HTML report
    generate_html_report: bool = True
    # Document-specific validators (e.g., "language_detection", "structural_completeness")
    document_validators: list[str] = Field(default_factory=list)


# ─── Packaging Settings ───────────────────────────────────────────

class PackagingSettings(BaseModel):
    """Configuration for the output packaging step."""
    # Number of preview rows for the free sample
    preview_rows: int = 100
    # Output formats
    output_csv: bool = True
    output_parquet: bool = True
    output_jsonl: bool = False  # JSON Lines — preferred for document datasets
    # Generate Gebru-style datasheet
    generate_datasheet: bool = True
    # Generate schema.json
    generate_schema: bool = True
    # Zip the final package
    create_zip: bool = True


# ─── Dataset Metadata ─────────────────────────────────────────────

class DatasetMetadata(BaseModel):
    """Top-level metadata for the dataset."""
    name: str
    version: str = "1.0.0"
    description: str
    language: str = "de"
    license: LicenseType = LicenseType.CC_BY_4
    author: str = "ML Upskill Agents UG"
    contact: str = "workflow.tools@icloud.com"
    tags: list[str] = Field(default_factory=list)
    # Intended use cases (for the datasheet)
    intended_uses: list[str] = Field(default_factory=list)
    # Out-of-scope uses (for the datasheet)
    out_of_scope_uses: list[str] = Field(default_factory=list)


# ─── Top-Level Config ─────────────────────────────────────────────

class DatasetConfig(BaseModel):
    """
    Complete configuration for a synthetic dataset.

    This is the root object parsed from a YAML config file.
    One config = one dataset = one generation run = one marketplace listing.

    A config can contain tabular tables (existing), document types + document
    tables (new), or both. Document-only configs omit the tables field entirely.
    """
    metadata: DatasetMetadata
    tables: list[TableDef] = Field(default_factory=list)
    # Document generation: blueprints + tables that reference them
    document_types: list[DocumentTypeDef] = Field(default_factory=list)
    document_tables: list[DocumentTableDef] = Field(default_factory=list)
    generation: GenerationSettings = Field(default_factory=GenerationSettings)
    validation: ValidationSettings = Field(default_factory=ValidationSettings)
    packaging: PackagingSettings = Field(default_factory=PackagingSettings)
