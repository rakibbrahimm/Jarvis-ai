import os
import requests


def _status_from_response(response):
    if response.status_code == 429:
        return "QUOTA_EXHAUSTED"
    if response.status_code in (401, 403):
        return "AUTH_ERROR"
    if response.status_code >= 500:
        return "PROVIDER_ERROR"
    if response.status_code >= 400:
        return f"HTTP_{response.status_code}"
    return "AVAILABLE"


def openai_status():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "NO_KEY"
    return "CONFIGURED"


def gemini_status():
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return "NO_KEY"
    return "CONFIGURED"


def perplexity_status():
    key = os.getenv("PERPLEXITY_API_KEY")
    if not key:
        return "NO_KEY"
    return "CONFIGURED"


def provider_status():
    return {
        "openai": openai_status(),
        "gemini": gemini_status(),
        "perplexity": perplexity_status(),
        "web": "AVAILABLE",
        "local_tools": "AVAILABLE",
    }
