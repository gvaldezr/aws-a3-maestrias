"""Test Scopus Abstract Retrieval with a known paper."""
import json
import boto3
import httpx

sm = boto3.client("secretsmanager")
resp = sm.get_secret_value(SecretId="academic-pipeline/dev/scopus-api-key")
api_key = json.loads(resp["SecretString"])["api_key"]

# Search for a well-known finance paper
search_resp = httpx.get(
    "https://api.elsevier.com/content/search/scopus",
    params={
        "query": 'TITLE-ABS-KEY("financial decision making") AND PUBYEAR > 2020',
        "count": 3,
        "sort": "citedby-count",
        "field": "dc:identifier,dc:title,dc:creator,dc:description,prism:publicationName,prism:coverDate,citedby-count,prism:doi,authkeywords",
    },
    headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
    timeout=15.0,
)
print(f"Search status: {search_resp.status_code}")

entries = search_resp.json().get("search-results", {}).get("entry", [])
print(f"Results: {len(entries)}")

for i, entry in enumerate(entries[:1]):
    print(f"\n{'='*60}")
    print(f"Paper {i+1}: {entry.get('dc:title', '')[:80]}")
    print(f"  dc:description present: {bool(entry.get('dc:description'))}")
    print(f"  dc:description length: {len(entry.get('dc:description', ''))}")
    if entry.get("dc:description"):
        print(f"  ABSTRACT: {entry['dc:description'][:300]}...")

    # Try Abstract Retrieval API
    scopus_id = entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")
    if scopus_id:
        print(f"\n  Fetching abstract for {scopus_id}...")
        abs_resp = httpx.get(
            f"https://api.elsevier.com/content/abstract/scopus_id/{scopus_id}",
            headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
            timeout=15.0,
        )
        print(f"  Abstract API status: {abs_resp.status_code}")
        if abs_resp.status_code == 200:
            core = abs_resp.json().get("abstracts-retrieval-response", {}).get("coredata", {})
            abstract = core.get("dc:description", "")
            print(f"  Abstract length: {len(abstract)} chars")
            print(f"  Abstract: {abstract[:400]}...")

            # Authors
            authors = abs_resp.json().get("abstracts-retrieval-response", {}).get("authors", {})
            auth_list = authors.get("author", []) if isinstance(authors, dict) else []
            print(f"  Authors: {len(auth_list)}")
            for a in auth_list[:5]:
                print(f"    - {a.get('ce:indexed-name', '')}")

            # Keywords
            auth_kw = abs_resp.json().get("abstracts-retrieval-response", {}).get("authkeywords", {})
            if auth_kw:
                kw_list = auth_kw.get("author-keyword", [])
                print(f"  Author keywords: {[k.get('$','') for k in kw_list[:10]]}")

            # Subject areas
            subj = abs_resp.json().get("abstracts-retrieval-response", {}).get("subject-areas", {})
            if subj:
                sa_list = subj.get("subject-area", [])
                print(f"  Subject areas: {[s.get('$','') for s in sa_list[:5]]}")
