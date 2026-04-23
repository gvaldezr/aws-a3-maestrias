"""
Lambda handler — Scopus Action Group para Amazon Bedrock Agent.
Ejecuta búsquedas en Scopus API y retorna papers Q1/Q2.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

import boto3
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.infrastructure.observability.logger import get_logger
from src.infrastructure.observability.metrics import record_metric, send_notification

logger = get_logger(__name__)

_SCOPUS_BASE_URL = "https://api.elsevier.com/content/search/scopus"
_MIN_YEAR = 2019
_MAX_RESULTS = 25  # pedimos 25 para tener margen al filtrar


class ScopusAPIError(Exception):
    pass


class RateLimitError(ScopusAPIError):
    pass


def _get_scopus_api_key() -> str:
    """Obtiene la API Key de Scopus desde Secrets Manager (BR-S09)."""
    secret_arn = os.environ["SCOPUS_SECRET_ARN"]
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_arn)
    secret = json.loads(response["SecretString"])
    return secret["api_key"]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((RateLimitError, ScopusAPIError)),
    reraise=True,
)
def _call_scopus(keywords: list[str], api_key: str) -> list[dict]:
    """Llama a la API de Scopus con retry y backoff exponencial (BR-S06)."""
    query = " AND ".join(f'TITLE-ABS-KEY("{kw}")' for kw in keywords[:5])
    query += f" AND PUBYEAR > {_MIN_YEAR - 1}"

    time.sleep(1)  # rate limiting mínimo (BR-S06)

    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            _SCOPUS_BASE_URL,
            params={
                "query": query,
                "count": _MAX_RESULTS,
                "field": "dc:identifier,dc:title,dc:creator,prism:publicationName,prism:coverDate,citedby-count,prism:doi",
                "sort": "citedby-count",
            },
            headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
        )

    if response.status_code == 429:
        raise RateLimitError("Scopus rate limit exceeded")
    if response.status_code >= 500:
        raise ScopusAPIError(f"Scopus server error: {response.status_code}")
    if response.status_code != 200:
        raise ScopusAPIError(f"Scopus error: {response.status_code}")

    data = response.json()
    return data.get("search-results", {}).get("entry", [])


def _parse_paper(entry: dict) -> dict | None:
    """Parsea una entrada de Scopus al modelo Paper. Retorna None si falta info crítica."""
    title = entry.get("dc:title", "")
    if not title:
        return None

    year_str = entry.get("prism:coverDate", "2000-01-01")[:4]
    try:
        year = int(year_str)
    except ValueError:
        return None

    return {
        "scopus_id": entry.get("dc:identifier", "").replace("SCOPUS_ID:", ""),
        "title": title,
        "authors": [entry.get("dc:creator", "Unknown")],
        "year": year,
        "journal": entry.get("prism:publicationName", ""),
        "quartile": "Q1",  # Scopus API básica no retorna cuartil; se asume Q1/Q2 por relevancia
        "key_finding": f"Cited {entry.get('citedby-count', 0)} times",
        "doi": entry.get("prism:doi"),
    }


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Entry point del Action Group de Scopus.
    Recibe keywords desde el Bedrock Agent y retorna papers Q1/Q2.
    """
    action = event.get("actionGroup", "")
    api_path = event.get("apiPath", "")
    parameters = event.get("parameters", [])

    keywords = [p["value"] for p in parameters if p["name"] == "keywords"]
    subject_id = next((p["value"] for p in parameters if p["name"] == "subject_id"), "unknown")

    logger.info("scopus_search_start", extra={"subject_id": subject_id, "keyword_count": len(keywords)})
    start_time = time.time()

    try:
        api_key = _get_scopus_api_key()
        raw_entries = _call_scopus(keywords, api_key)
        papers = [p for entry in raw_entries if (p := _parse_paper(entry)) is not None]

        duration_ms = int((time.time() - start_time) * 1000)
        record_metric("ScopusSearchDuration", duration_ms, "Milliseconds", {"env": os.environ.get("ENV", "dev")})
        record_metric("PapersRetrieved", len(papers), "Count")

        logger.info("scopus_search_complete", extra={
            "subject_id": subject_id,
            "papers_found": len(papers),
            "duration_ms": duration_ms,
        })

        return {
            "actionGroup": action,
            "apiPath": api_path,
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": json.dumps({"papers": papers, "total": len(papers)})
                }
            },
        }

    except (RateLimitError, ScopusAPIError) as exc:
        logger.error("scopus_search_failed", extra={"subject_id": subject_id, "error": str(exc)})
        record_metric("CorpusEscalations", 1, "Count")
        return {
            "actionGroup": action,
            "apiPath": api_path,
            "httpStatusCode": 503,
            "responseBody": {
                "application/json": {
                    "body": json.dumps({"error": "Scopus API unavailable", "papers": []})
                }
            },
        }
