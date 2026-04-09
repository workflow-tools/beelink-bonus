"""
LLM triage — sends diffs to Ollama for classification.

Takes a URL diff and watch context, formats the triage prompt using
the product's prompt template, calls Ollama's /api/generate endpoint,
and parses the structured JSON response.

Rule 5: Ollama Sharing — RegWatch shares the Ollama instance with Data Forge.
Requests queue behind any running inference jobs. This is acceptable because
regulatory changes aren't sub-second urgent.
"""

import json
import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

# Ollama defaults — configurable via environment variables
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_TIMEOUT = 120  # seconds — generous for queued requests


def triage_change(
    url: str,
    diff_text: str,
    watch_config: dict,
    prompt_config: Optional[dict],
    ollama_url: str = None,
    model: str = None,
) -> dict[str, Any]:
    """Send a detected change to Ollama for triage classification.

    Args:
        url: The URL that changed.
        diff_text: The text diff of the change.
        watch_config: The watch entry from watches/*.yaml.
        prompt_config: The triage prompt from prompts/*_triage.yaml.
        ollama_url: Override Ollama base URL.
        model: Override Ollama model name.

    Returns:
        Parsed triage result dict with keys like:
            relevance, urgency, affected_corridors, summary, etc.
        Falls back to a structured error dict if parsing fails.
    """
    base_url = ollama_url or OLLAMA_BASE_URL
    model_name = model or OLLAMA_MODEL

    # Build the prompt from template
    system_prompt, user_prompt = _build_prompt(url, diff_text, watch_config, prompt_config)

    # Call Ollama
    response_text = _call_ollama(base_url, model_name, system_prompt, user_prompt)

    # Parse structured JSON from response
    triage_result = _parse_triage_response(response_text, url)

    return triage_result


def _build_prompt(
    url: str,
    diff_text: str,
    watch_config: dict,
    prompt_config: Optional[dict],
) -> tuple[str, str]:
    """Build system and user prompts from template and watch context.

    Args:
        url: The changed URL.
        diff_text: The diff text.
        watch_config: Watch entry with context fields.
        prompt_config: Prompt template with 'system' and 'template' keys.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    context = watch_config.get("context", {})

    if prompt_config:
        system_prompt = prompt_config.get("system", "You are a regulatory change analyst.")
        template = prompt_config.get("template", "Analyze this change:\n{diff_text}")
    else:
        system_prompt = "You are a regulatory change analyst."
        template = (
            "A monitored web page has changed. Classify the change.\n\n"
            "URL: {url}\n\nDIFF:\n---\n{diff_text}\n---\n\n"
            'Respond in JSON with keys: relevance, urgency, summary, recommended_action.'
        )

    # Populate template with context fields
    template_vars = {
        "url": url,
        "diff_text": diff_text[:4000],  # Truncate very large diffs
        "corridors": context.get("corridors", []),
        "likely_steps": context.get("likely_steps", []),
        "likely_fields": context.get("likely_fields", []),
        "note": context.get("note", ""),
        "categories": context.get("categories", []),
    }

    user_prompt = template.format(**template_vars)

    return system_prompt, user_prompt


def _call_ollama(
    base_url: str, model: str, system_prompt: str, user_prompt: str
) -> str:
    """Call Ollama's generate API and return the response text.

    Args:
        base_url: Ollama API base URL.
        model: Model name (e.g., 'llama3.1:8b').
        system_prompt: System message for the LLM.
        user_prompt: User message with the diff and context.

    Returns:
        Raw text response from Ollama.

    Raises:
        requests.RequestException: If the Ollama API is unreachable.
        RuntimeError: If the response indicates an error.
    """
    endpoint = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for consistent classification
            "num_predict": 1024,
        },
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
    except requests.ConnectionError:
        raise RuntimeError(
            f"Cannot reach Ollama at {base_url}. "
            "Is Ollama running? (ollama serve)"
        )
    except requests.Timeout:
        raise RuntimeError(
            f"Ollama triage timed out after {OLLAMA_TIMEOUT}s. "
            "A large model may be loaded — triage queued behind it."
        )

    data = resp.json()
    return data.get("response", "")


def _parse_triage_response(response_text: str, url: str) -> dict[str, Any]:
    """Parse the LLM's JSON response into a structured triage result.

    Attempts to extract JSON from the response. If parsing fails,
    returns a fallback result with the raw text for human review.

    Args:
        response_text: Raw text from Ollama.
        url: The URL that was triaged (for context in fallback).

    Returns:
        Parsed triage dict.
    """
    # Try to find JSON in the response (LLMs sometimes wrap in markdown)
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        result = json.loads(text)
        if isinstance(result, dict):
            result["_raw_response"] = None  # Parsed successfully
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON within the text
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            result = json.loads(text[start:end])
            if isinstance(result, dict):
                result["_raw_response"] = None
                return result
        except json.JSONDecodeError:
            pass

    # Fallback: return raw response for human review
    logger.warning(f"Could not parse triage JSON for {url}")
    return {
        "relevance": "UNCLEAR",
        "urgency": "P2",
        "summary": "LLM response could not be parsed as JSON. Manual review needed.",
        "recommended_action": "Review raw response below.",
        "_raw_response": response_text[:2000],
        "_parse_error": True,
    }
