"""Test Scopus Abstract Retrieval API to see what data is available."""
import json
import boto3
import httpx

# Get API key from Secrets Manager
sm = boto3.client("secretsmanager")
resp = sm.get_secret_value(SecretId="academic-pipeline/dev/scopus-api-key")
api_key = json.loads(resp["SecretString"])["api_key"]
print(f"API Key: {api_key[:8]}...")

# Use a known Scopus ID from our papers
# First, search for a paper to get a real Scopus ID
search_resp = httpx.get(
    "https://api.elsevier.com/content/search/scopus",
    params={
        "query": 'TITLE("corporate finance strategic decisions")',
        "count": 1,
        "field": "dc:identifier,dc:title,dc:creator,dc:description,prism:publicationName,prism:coverDate,citedby-count,prism:doi,authkeywords",
    },
    headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
    timeout=15.0,
)
print(f"\nSearch status: {search_resp.status_code}")

if search_resp.status_code == 200:
    entries = search_resp.json().get("search-results", {}).get("entry", [])
    if entries:
        entry = entries[0]
        print(f"\n=== SEARCH RESULT FIELDS ===")
        for k, v in entry.items():
            print(f"  {k}: {str(v)[:150]}")

        scopus_id = entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")
        print(f"\nScopus ID: {scopus_id}")

        # Now try Abstract Retrieval API
        print(f"\n=== ABSTRACT RETRIEVAL API ===")
        abs_resp = httpx.get(
            f"https://api.elsevier.com/content/abstract/scopus_id/{scopus_id}",
            headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
            timeout=15.0,
        )
        print(f"Abstract API status: {abs_resp.status_code}")

        if abs_resp.status_code == 200:
            abs_data = abs_resp.json()
            core = abs_data.get("abstracts-retrieval-response", {}).get("coredata", {})
            print(f"\n=== COREDATA FIELDS ===")
            for k, v in core.items():
                print(f"  {k}: {str(v)[:200]}")

            # Check for abstract text
            abstract = core.get("dc:description", "")
            print(f"\n=== ABSTRACT ({len(abstract)} chars) ===")
            print(abstract[:500])

            # Check for author keywords
            auth_kw = abs_data.get("abstracts-retrieval-response", {}).get("authkeywords", {})
            print(f"\n=== AUTHOR KEYWORDS ===")
            print(json.dumps(auth_kw, indent=2)[:300])

            # Check for subject areas
            subj = abs_data.get("abstracts-retrieval-response", {}).get("subject-areas", {})
            print(f"\n=== SUBJECT AREAS ===")
            print(json.dumps(subj, indent=2)[:300])
        else:
            print(f"Abstract API error: {abs_resp.text[:200]}")
    else:
        print("No search results")
else:
    print(f"Search error: {search_resp.text[:200]}")
