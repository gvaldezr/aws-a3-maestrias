"""
Agente Scholar — AgentCore Runtime + Strands SDK.
Fases 1 y 2: Ingesta y Búsqueda + Elicitación Académica.

Patrón: BedrockAgentCoreApp + @app.entrypoint + lazy Strands Agent
"""
from __future__ import annotations

import json
import os
import re

import boto3
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext

app = BedrockAgentCoreApp()

# Lazy-initialized globals
_scholar_agent = None


def _get_agent():
    """Lazy init — only create Strands Agent on first invocation, not at import time."""
    global _scholar_agent
    if _scholar_agent is not None:
        return _scholar_agent

    from strands import Agent, tool
    from strands.models import BedrockModel

    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-6",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        temperature=0.0,
        max_tokens=16384,
    )

    @tool
    def search_scopus_papers(keywords: list, subject_id: str) -> dict:
        """Search Scopus API for Q1/Q2 academic papers using the given keywords.

        Args:
            keywords: Search keywords derived from learning outcomes
            subject_id: The subject identifier for logging
        """
        import time
        import boto3
        import httpx

        def _get_api_key() -> str:
            secret_arn = os.environ.get("SCOPUS_SECRET_ARN", "arn:aws:secretsmanager:us-east-1:254508868459:secret:academic-pipeline/dev/scopus-api-key-CrgImQ")
            if not secret_arn:
                return ""
            client = boto3.client("secretsmanager")
            resp = client.get_secret_value(SecretId=secret_arn)
            return json.loads(resp["SecretString"]).get("api_key", "")

        try:
            api_key = _get_api_key()
            if not api_key:
                return {"papers": [], "total": 0, "error": "No Scopus API key configured"}

            query = " AND ".join(f'TITLE-ABS-KEY("{kw}")' for kw in keywords[:5])
            query += " AND PUBYEAR > 2018"
            time.sleep(1)

            with httpx.Client(timeout=30.0) as client:
                resp = client.get(
                    "https://api.elsevier.com/content/search/scopus",
                    params={"query": query, "count": 25, "sort": "citedby-count",
                            "field": "dc:identifier,dc:title,dc:creator,prism:publicationName,prism:coverDate,citedby-count,prism:doi"},
                    headers={"X-ELS-APIKey": api_key, "Accept": "application/json"},
                )

            if resp.status_code != 200:
                return {"papers": [], "total": 0, "error": f"Scopus API error: {resp.status_code}"}

            entries = resp.json().get("search-results", {}).get("entry", [])
            papers = []
            for e in entries:
                title = e.get("dc:title", "")
                if not title:
                    continue
                try:
                    year = int(e.get("prism:coverDate", "2000")[:4])
                except ValueError:
                    continue
                papers.append({
                    "scopus_id": e.get("dc:identifier", "").replace("SCOPUS_ID:", ""),
                    "title": title,
                    "authors": [e.get("dc:creator", "Unknown")],
                    "year": year,
                    "journal": e.get("prism:publicationName", ""),
                    "quartile": "Q1",
                    "key_finding": f"Cited {e.get('citedby-count', 0)} times",
                    "doi": e.get("prism:doi"),
                })
            return {"papers": papers, "total": len(papers)}
        except Exception as exc:
            return {"papers": [], "total": 0, "error": str(exc)}

    @tool
    def build_knowledge_matrix(papers: list, learning_outcomes: list) -> dict:
        """Extract concepts and methodologies from papers to build the Knowledge Matrix.

        Args:
            papers: List of paper dicts with title, authors, year, journal, key_finding
            learning_outcomes: List of learning outcome dicts with ra_id and description
        """
        matrix = []
        for paper in papers[:20]:
            paper_text = (paper.get("title", "") + " " + paper.get("key_finding", "")).lower()
            relevant_ras = [
                lo["ra_id"] for lo in learning_outcomes
                if any(w in paper_text for w in lo["description"].lower().split() if len(w) > 4)
            ]
            matrix.append({
                "concept": paper.get("title", ""),
                "source_paper_id": paper.get("scopus_id", ""),
                "methodology": f"From: {paper.get('journal', '')}",
                "executive_application": paper.get("key_finding", ""),
                "ra_relevance": relevant_ras or [learning_outcomes[0]["ra_id"]] if learning_outcomes else [],
            })
        return {"knowledge_matrix": matrix}

    _scholar_agent = Agent(
        model=model,
        tools=[search_scopus_papers, build_knowledge_matrix],
        system_prompt=(
            "You are Scholar, an academic research agent. "
            "Use search_scopus_papers to find Q1/Q2 papers, then build_knowledge_matrix to extract concepts. "
            "Return JSON with keys: top20_papers, knowledge_matrix, keywords_used"
        ),
    )
    return _scholar_agent


@app.entrypoint
def invoke(payload: dict, context: RequestContext = None) -> dict:
    """AgentCore Runtime entrypoint for Scholar Agent."""
    prompt = payload.get("prompt", "")
    subject_id = payload.get("subject_id", "")

    if not prompt and not subject_id:
        return {"result": "Scholar Agent ready. Send a prompt or subject_id to begin research."}

    agent = _get_agent()

    if subject_id:
        prompt = json.dumps({
            "task": "Research academic papers for this subject",
            "subject_id": subject_id,
            "instructions": "Use search_scopus_papers and build_knowledge_matrix tools",
        })

    result = agent(prompt)
    result_str = str(result)

    # Self-persist: if subject_id provided, write results to S3 + DynamoDB
    if subject_id:
        try:
            _self_persist(subject_id, result_str, "research", "KNOWLEDGE_MATRIX_READY", "scholar-agent")
        except Exception as e:
            import logging
            logging.getLogger().error(f"PERSIST_ERROR: {e}")

    return {"result": result_str}


def _self_persist(subject_id: str, result_text: str, section: str, new_state: str, agent_name: str) -> None:
    """Write agent results directly to S3 JSON and update DynamoDB."""
    from datetime import datetime, timezone

    bucket = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
    table_name = os.environ.get("SUBJECTS_TABLE_NAME", "academic-pipeline-subjects-dev")

    s3 = boto3.client("s3")
    ddb = boto3.resource("dynamodb")

    # Read current JSON
    obj = s3.get_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json")
    sj = json.loads(obj["Body"].read().decode("utf-8"))

    # Parse JSON from agent response
    parsed = {}
    # Try ```json blocks
    matches = re.findall(r'```(?:json)?\s*\n(.*?)\n```', result_text, re.DOTALL)
    for m in matches:
        try:
            p = json.loads(m.strip())
            if isinstance(p, dict) and len(p) > len(parsed):
                parsed = p
        except json.JSONDecodeError:
            continue
    # Try direct parse
    if not parsed:
        try:
            parsed = json.loads(result_text)
        except (json.JSONDecodeError, TypeError):
            pass

    # Persist based on section
    if section == "research":
        sj.setdefault("research", {})
        if parsed.get("top20_papers"):
            sj["research"]["top20_papers"] = parsed["top20_papers"]
        if parsed.get("knowledge_matrix"):
            sj["research"]["knowledge_matrix"] = parsed["knowledge_matrix"]
        if parsed.get("keywords_used"):
            sj["research"]["keywords"] = parsed["keywords_used"]

    # Update state
    now = datetime.now(timezone.utc).isoformat()
    sj["pipeline_state"]["current_state"] = new_state
    sj["pipeline_state"]["state_history"].append({
        "state": new_state, "agent": agent_name,
        "timestamp": now, "llm_version": "claude-sonnet-4.6", "result_hash": "",
    })
    sj["updated_at"] = now

    # Write back to S3
    s3.put_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json",
                  Body=json.dumps(sj, ensure_ascii=False, indent=2).encode("utf-8"),
                  ContentType="application/json")

    # Update DynamoDB
    ddb.Table(table_name).put_item(Item={
        "subject_id": subject_id, "SK": "STATE",
        "current_state": new_state,
        "subject_name": sj["metadata"]["subject_name"],
        "program_name": sj["metadata"]["program_name"],
        "updated_at": now,
        "s3_key": f"subjects/{subject_id}/subject.json",
    })


if __name__ == "__main__":
    app.run()
