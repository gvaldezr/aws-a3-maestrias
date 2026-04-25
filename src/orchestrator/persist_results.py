"""
Persist agent results back to the Subject JSON in S3.
Called by Step Functions after each agent completes.
Handles Markdown-wrapped JSON responses from AgentCore agents.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

import boto3

BUCKET = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
TABLE = os.environ.get("SUBJECTS_TABLE_NAME", "academic-pipeline-subjects-dev")


def _extract_json(result: dict) -> dict:
    """Extract JSON from agent response — handles Markdown-wrapped JSON."""
    raw = result.get("result", "")
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    text = str(raw)

    # 1. Direct JSON parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Extract from ```json ... ``` blocks (largest one)
    matches = re.findall(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    best = {}
    for m in matches:
        try:
            parsed = json.loads(m.strip())
            if isinstance(parsed, dict) and len(parsed) > len(best):
                best = parsed
        except json.JSONDecodeError:
            continue
    if best:
        return best

    # 3. Find largest JSON object in text
    brace_start = text.find('{')
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[brace_start:i+1])
                    except json.JSONDecodeError:
                        break
    return {}


def _get_json(s3, subject_id: str) -> dict:
    obj = s3.get_object(Bucket=BUCKET, Key=f"subjects/{subject_id}/subject.json")
    return json.loads(obj["Body"].read().decode("utf-8"))


def _save_json(s3, subject_id: str, data: dict) -> None:
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    s3.put_object(Bucket=BUCKET, Key=f"subjects/{subject_id}/subject.json",
                  Body=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
                  ContentType="application/json")
    ddb = boto3.resource("dynamodb")
    ddb.Table(TABLE).put_item(Item={
        "subject_id": subject_id, "SK": "STATE",
        "current_state": data["pipeline_state"]["current_state"],
        "subject_name": data["metadata"]["subject_name"],
        "program_name": data["metadata"]["program_name"],
        "updated_at": data["updated_at"],
        "s3_key": f"subjects/{subject_id}/subject.json",
    })


def _add_history(sj: dict, state: str, agent: str) -> None:
    sj["pipeline_state"]["current_state"] = state
    sj["pipeline_state"]["state_history"].append({
        "state": state, "agent": agent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_version": "claude-sonnet-4.6", "result_hash": "",
    })


def persist_scholar(event: dict, context: Any) -> dict:
    subject_id = event.get("subject_id") or event.get("scholar", {}).get("subject_id", "")
    raw_result = event.get("scholar", {}).get("result", {})
    parsed = _extract_json(raw_result)
    
    # Log what we received and parsed
    import logging
    logging.getLogger().setLevel(logging.INFO)
    logging.info(f"PERSIST_SCHOLAR raw_keys={list(raw_result.keys()) if isinstance(raw_result, dict) else type(raw_result).__name__}")
    logging.info(f"PERSIST_SCHOLAR parsed_keys={list(parsed.keys())}")
    
    s3 = boto3.client("s3")
    sj = _get_json(s3, subject_id)

    sj.setdefault("research", {})
    if parsed.get("top20_papers"):
        sj["research"]["top20_papers"] = parsed["top20_papers"]
    if parsed.get("knowledge_matrix"):
        sj["research"]["knowledge_matrix"] = parsed["knowledge_matrix"]
    if parsed.get("keywords_used"):
        sj["research"]["keywords"] = parsed["keywords_used"]

    _add_history(sj, "KNOWLEDGE_MATRIX_READY", "scholar-agent")
    _save_json(s3, subject_id, sj)
    return {"subject_id": subject_id, "state": "KNOWLEDGE_MATRIX_READY",
            "papers_persisted": len(sj["research"].get("top20_papers", []))}


def persist_di(event: dict, context: Any) -> dict:
    subject_id = event.get("subject_id") or event.get("di", {}).get("subject_id", "")
    parsed = _extract_json(event.get("di", {}).get("result", {}))
    s3 = boto3.client("s3")
    sj = _get_json(s3, subject_id)

    sj.setdefault("instructional_design", {})
    if parsed.get("objectives"):
        sj["instructional_design"]["learning_objectives"] = parsed["objectives"]
    if parsed.get("traceability_matrix"):
        sj["instructional_design"]["traceability_matrix"] = parsed["traceability_matrix"]
    if parsed.get("descriptive_card"):
        sj["instructional_design"]["descriptive_card"] = parsed["descriptive_card"]
    if parsed.get("content_map"):
        sj["instructional_design"]["content_map"] = parsed["content_map"]

    _add_history(sj, "DI_READY", "di-agent")
    _save_json(s3, subject_id, sj)
    return {"subject_id": subject_id, "state": "DI_READY",
            "objectives_persisted": len(sj["instructional_design"].get("learning_objectives", []))}


def persist_content(event: dict, context: Any) -> dict:
    subject_id = event.get("subject_id") or event.get("content", {}).get("subject_id", "")
    parsed = _extract_json(event.get("content", {}).get("result", {}))
    s3 = boto3.client("s3")
    sj = _get_json(s3, subject_id)

    sj.setdefault("content_package", {})
    if parsed.get("executive_readings"):
        sj["content_package"]["executive_readings"] = parsed["executive_readings"]
    if parsed.get("quizzes"):
        sj["content_package"]["quizzes"] = parsed["quizzes"]
    if parsed.get("maestria_artifacts"):
        sj["content_package"]["maestria_artifacts"] = parsed["maestria_artifacts"]
    if parsed.get("lab_cases"):
        sj["content_package"]["lab_cases"] = parsed["lab_cases"]

    _add_history(sj, "CONTENT_READY", "content-agent")
    _save_json(s3, subject_id, sj)
    return {"subject_id": subject_id, "state": "CONTENT_READY",
            "quizzes_persisted": len(sj["content_package"].get("quizzes", [])),
            "has_maestria": bool(sj["content_package"].get("maestria_artifacts"))}
