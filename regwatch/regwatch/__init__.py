"""
RegWatch — Self-hosted, LLM-triaged web change detection system.

Monitors regulatory and policy URLs, classifies detected changes by urgency
and domain impact using a local LLM (Ollama), and routes structured
notifications to the right product.

Architecture:
    changedetection.io (polling) → webhook → regwatch (triage via Ollama)
    → notify (email/GitHub/log) → product queries via REST API

Configuration is entirely YAML-driven:
    domains.yaml       — product registry + notification routing
    watches/*.yaml     — per-product URL watch lists
    prompts/*.yaml     — per-product LLM triage prompt templates
"""

__version__ = "0.1.0"
