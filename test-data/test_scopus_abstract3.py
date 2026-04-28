"""Test all Scopus API approaches for getting abstracts."""
import json
import boto3
import httpx

sm = boto3.client("secretsmanager")
resp = sm.get_secret_value(SecretId="academic-pipeline/dev/scopus-api-key")
api_key = json.loads(resp["SecretString"])["api_key"]
headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}

# Approach 1: Search API with dc:description field
print("=== Approach 1: Search API with description field ===")
r1 = httpx.get(
    "https://api.elsevier.com/content/search/scopus",
    params={
        "query": 'TITLE("machine learning") AND TITLE("finance") AND PUBYEAR > 2022',
        "count": 2,
        "sort": "citedby-count",
        "field": "dc:identifier,dc:title,dc:description,dc:creator,prism:publicationName,prism:coverDate,citedby-count,prism:doi,authkeywords,prism:aggregationType",
    },
    headers=headers,
    timeout=15.0,
)
entries = r1.json().get("search-results", {}).get("entry", [])
print(f"Results: {len(entries)}")
for e in entries[:2]:
    print(f"  Title: {e.get('dc:title', '')[:80]}")
    desc = e.get("dc:description", "")
    print(f"  Description: {len(desc)} chars -> {desc[:200]}")
    print(f"  All keys: {list(e.keys())}")
    sid = e.get("dc:identifier", "").replace("SCOPUS_ID:", "")

    # Approach 2: Abstract Retrieval with full view
    if sid:
        print(f"\n=== Approach 2: Abstract Retrieval (scopus_id={sid}) ===")
        r2 = httpx.get(
            f"https://api.elsevier.com/content/abstract/scopus_id/{sid}",
            params={"view": "FULL"},
            headers=headers,
            timeout=15.0,
        )
        print(f"  Status: {r2.status_code}")
        if r2.status_code == 200:
            data = r2.json().get("abstracts-retrieval-response", {})
            core = data.get("coredata", {})
            print(f"  Coredata keys: {list(core.keys())}")
            abstract = core.get("dc:description", "")
            print(f"  Abstract: {len(abstract)} chars")
            if abstract:
                print(f"  Text: {abstract[:300]}...")

            # Try item.description
            item = data.get("item", {})
            if item:
                bibrecord = item.get("bibrecord", {})
                head = bibrecord.get("head", {})
                abstracts = head.get("abstracts", "")
                print(f"  item.bibrecord.head.abstracts: {len(str(abstracts))} chars")
                if abstracts:
                    print(f"  Text: {str(abstracts)[:300]}...")

    # Approach 3: DOI-based retrieval
    doi = e.get("prism:doi", "")
    if doi:
        print(f"\n=== Approach 3: DOI retrieval ({doi}) ===")
        r3 = httpx.get(
            f"https://api.elsevier.com/content/abstract/doi/{doi}",
            params={"view": "FULL"},
            headers=headers,
            timeout=15.0,
        )
        print(f"  Status: {r3.status_code}")
        if r3.status_code == 200:
            core3 = r3.json().get("abstracts-retrieval-response", {}).get("coredata", {})
            abs3 = core3.get("dc:description", "")
            print(f"  Abstract: {len(abs3)} chars -> {abs3[:200]}")

    break  # Only test first paper
