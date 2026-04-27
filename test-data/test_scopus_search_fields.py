"""Test what fields the Scopus Search API actually returns."""
import json
import boto3
import httpx

sm = boto3.client("secretsmanager")
resp = sm.get_secret_value(SecretId="academic-pipeline/dev/scopus-api-key")
api_key = json.loads(resp["SecretString"])["api_key"]

# Request ALL available fields
r = httpx.get(
    "https://api.elsevier.com/content/search/scopus",
    params={
        "query": 'TITLE-ABS-KEY("financial analytics") AND PUBYEAR > 2022',
        "count": 1,
        "sort": "citedby-count",
    },
    headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
    timeout=15.0,
)
entries = r.json().get("search-results", {}).get("entry", [])
if entries:
    print("=== ALL FIELDS RETURNED BY SEARCH API ===")
    for k, v in entries[0].items():
        val = str(v)
        print(f"  {k}: {val[:200]}")
    print(f"\nTotal fields: {len(entries[0])}")
