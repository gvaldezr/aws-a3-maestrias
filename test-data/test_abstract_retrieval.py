"""Test Scopus Abstract Retrieval API with correct format."""
import json
import boto3
import httpx

sm = boto3.client("secretsmanager")
resp = sm.get_secret_value(SecretId="academic-pipeline/dev/scopus-api-key")
api_key = json.loads(resp["SecretString"])["api_key"]

# Step 1: Search to get a Scopus ID
print("Step 1: Search API")
r1 = httpx.get(
    "https://api.elsevier.com/content/search/scopus",
    params={
        "query": 'TITLE-ABS-KEY("financial analytics") AND PUBYEAR > 2022',
        "count": 1,
        "sort": "citedby-count",
    },
    headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
    timeout=15.0,
)
entries = r1.json().get("search-results", {}).get("entry", [])
if not entries:
    print("No results")
    exit()

scopus_id = entries[0].get("dc:identifier", "").replace("SCOPUS_ID:", "")
title = entries[0].get("dc:title", "")
print(f"  Found: {title[:60]} (ID: {scopus_id})")

# Step 2: Abstract Retrieval API - try different approaches
print("\nStep 2: Abstract Retrieval API")

# Approach A: Standard with httpAccept header
print("\n  Approach A: httpAccept=application/json")
r2a = httpx.get(
    f"https://api.elsevier.com/content/abstract/scopus_id/{scopus_id}",
    headers={
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
    },
    timeout=15.0,
)
print(f"  Status: {r2a.status_code}")
if r2a.status_code == 200:
    data = r2a.json()
    core = data.get("abstracts-retrieval-response", {}).get("coredata", {})
    abstract = core.get("dc:description", "")
    print(f"  Abstract: {len(abstract)} chars")
    if abstract:
        print(f"  Text: {abstract[:300]}")
    else:
        print(f"  Coredata keys: {list(core.keys())}")
elif r2a.status_code == 401:
    error_body = r2a.json() if r2a.headers.get("content-type", "").startswith("application/json") else r2a.text
    print(f"  401 Error: {json.dumps(error_body)[:300]}")
else:
    print(f"  Error: {r2a.text[:200]}")

# Approach B: With insttoken (institutional token)
print("\n  Approach B: With view=META_ABS")
r2b = httpx.get(
    f"https://api.elsevier.com/content/abstract/scopus_id/{scopus_id}",
    params={"view": "META_ABS"},
    headers={
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
    },
    timeout=15.0,
)
print(f"  Status: {r2b.status_code}")
if r2b.status_code == 200:
    data = r2b.json()
    core = data.get("abstracts-retrieval-response", {}).get("coredata", {})
    abstract = core.get("dc:description", "")
    print(f"  Abstract: {len(abstract)} chars")
    if abstract:
        print(f"  Text: {abstract[:300]}")

# Approach C: Using EID instead of scopus_id
eid = entries[0].get("eid", "")
if eid:
    print(f"\n  Approach C: Using EID ({eid})")
    r2c = httpx.get(
        f"https://api.elsevier.com/content/abstract/eid/{eid}",
        headers={
            "X-ELS-APIKey": api_key,
            "Accept": "application/json",
        },
        timeout=15.0,
    )
    print(f"  Status: {r2c.status_code}")
    if r2c.status_code == 200:
        data = r2c.json()
        core = data.get("abstracts-retrieval-response", {}).get("coredata", {})
        abstract = core.get("dc:description", "")
        print(f"  Abstract: {len(abstract)} chars")
        if abstract:
            print(f"  Text: {abstract[:300]}")

# Approach D: Check API key entitlements
print("\n  Approach D: Check API key entitlements")
r3 = httpx.get(
    "https://api.elsevier.com/authenticate",
    params={"platform": "SCOPUS"},
    headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
    timeout=15.0,
)
print(f"  Auth status: {r3.status_code}")
print(f"  Response: {r3.text[:300]}")
