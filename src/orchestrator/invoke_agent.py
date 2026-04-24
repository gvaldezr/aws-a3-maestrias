"""
Invoke AgentCore Runtime agents from Step Functions via HTTP.
Uses the AgentCore Runtime invoke API directly.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any

import boto3

from src.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

SCHOLAR_ARN = os.environ.get("SCHOLAR_RUNTIME_ARN", "")
DI_ARN = os.environ.get("DI_RUNTIME_ARN", "")
CONTENT_ARN = os.environ.get("CONTENT_RUNTIME_ARN", "")


def warm_up_agents(event: dict, context: Any) -> dict:
    """Pre-warm all 3 AgentCore agents with a simple ping. Called once at pipeline start."""
    import time
    region = os.environ.get("AWS_REGION", "us-east-1")
    client = boto3.client("bedrock-agentcore", region_name=region)
    results = {}

    for name, arn in [("scholar", SCHOLAR_ARN), ("di", DI_ARN), ("content", CONTENT_ARN)]:
        if not arn:
            results[name] = "skipped"
            continue
        session_id = f"warmup-{uuid.uuid4().hex}-{uuid.uuid4().hex[:8]}"
        for attempt in range(3):
            try:
                resp = client.invoke_agent_runtime(
                    agentRuntimeArn=arn,
                    qualifier="DEFAULT",
                    runtimeSessionId=session_id,
                    payload=json.dumps({"prompt": "ping"}).encode("utf-8"),
                )
                body = resp.get("body", b"")
                if hasattr(body, "read"):
                    body.read()
                results[name] = "warm"
                logger.info("warmup_ok", extra={"agent": name, "attempt": attempt + 1})
                break
            except Exception as e:
                if attempt < 2:
                    logger.info("warmup_retry", extra={"agent": name, "attempt": attempt + 1, "error": str(e)[:100]})
                    time.sleep(15)
                    session_id = f"warmup-{uuid.uuid4().hex}-{uuid.uuid4().hex[:8]}"
                else:
                    results[name] = f"failed: {str(e)[:80]}"
                    logger.error("warmup_failed", extra={"agent": name, "error": str(e)[:100]})

    return {"subject_id": event.get("subject_id", ""), "warmup": results}


def _invoke_runtime(runtime_arn: str, payload: dict) -> dict:
    """Invoke AgentCore Runtime via boto3 bedrock-agent-runtime."""
    import uuid
    region = os.environ.get("AWS_REGION", "us-east-1")
    runtime_id = runtime_arn.split("/")[-1]
    session_id = f"orch-{uuid.uuid4().hex}-{uuid.uuid4().hex[:8]}"

    try:
        client = boto3.client("bedrock-agentcore", region_name=region)
        
        # Retry up to 3 times for cold start timeouts
        last_error = None
        for attempt in range(3):
            try:
                response = client.invoke_agent_runtime(
                    agentRuntimeArn=runtime_arn,
                    qualifier="DEFAULT",
                    runtimeSessionId=session_id,
                    payload=json.dumps(payload).encode("utf-8"),
                )
                body = response.get("response") or response.get("body", b"")
                if hasattr(body, "read"):
                    body = body.read()
                if isinstance(body, bytes):
                    body = body.decode("utf-8")
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return {"result": body}
            except Exception as e:
                last_error = e
                if "500" in str(e) and attempt < 2:
                    import time
                    logger.info("agentcore_retry", extra={"runtime_id": runtime_id, "attempt": attempt + 1})
                    time.sleep(10)
                    session_id = f"orch-{uuid.uuid4().hex}-{uuid.uuid4().hex[:8]}"
                    continue
                raise
        
        return {"error": str(last_error)}
    except Exception as e:
        logger.error("agentcore_invoke_error", extra={"runtime_id": runtime_id, "error": str(e)})
        return {"error": str(e)}


def invoke_scholar(event: dict, context: Any) -> dict:
    """Step 1: Invoke Scholar Agent."""
    subject_id = event["subject_id"]
    logger.info("orchestrator_scholar_start", extra={"subject_id": subject_id})

    result = _invoke_runtime(SCHOLAR_ARN, {
        "subject_id": subject_id,
        "prompt": f"Research academic papers for subject {subject_id}. Use search_scopus_papers and build_knowledge_matrix tools.",
    })

    logger.info("orchestrator_scholar_complete", extra={"subject_id": subject_id})
    return {"subject_id": subject_id, "scholar_status": "complete", "result": result}


def invoke_di(event: dict, context: Any) -> dict:
    """Step 2: Invoke DI Agent."""
    subject_id = event.get("subject_id") or event.get("scholar", {}).get("subject_id", "")
    logger.info("orchestrator_di_start", extra={"subject_id": subject_id})

    result = _invoke_runtime(DI_ARN, {
        "subject_id": subject_id,
        "prompt": f"Design instructional content for subject {subject_id}. Use generate_learning_objectives and build_descriptive_card tools.",
    })

    logger.info("orchestrator_di_complete", extra={"subject_id": subject_id})
    return {"subject_id": subject_id, "di_status": "complete", "result": result}


def invoke_content(event: dict, context: Any) -> dict:
    """Step 3: Invoke Content Agent."""
    subject_id = event.get("subject_id") or event.get("di", {}).get("subject_id", "")
    logger.info("orchestrator_content_start", extra={"subject_id": subject_id})

    result = _invoke_runtime(CONTENT_ARN, {
        "subject_id": subject_id,
        "prompt": f"Generate complete content package for subject {subject_id}. This is a MAESTRIA program. Use all tools.",
    })

    logger.info("orchestrator_content_complete", extra={"subject_id": subject_id})
    return {"subject_id": subject_id, "content_status": "complete", "result": result}


def invoke_qa_gate(event: dict, context: Any) -> dict:
    """Step 4: Invoke QA Gate Lambda."""
    subject_id = event.get("subject_id") or event.get("content", {}).get("subject_id", "")
    logger.info("orchestrator_qa_start", extra={"subject_id": subject_id})

    lambda_client = boto3.client("lambda")
    qa_function = os.environ.get("QA_GATE_FUNCTION_NAME", "academic-pipeline-qa-gate-dev")

    response = lambda_client.invoke(
        FunctionName=qa_function,
        InvocationType="RequestResponse",
        Payload=json.dumps({"subject_id": subject_id}),
    )

    result = json.loads(response["Payload"].read().decode("utf-8"))
    body = json.loads(result.get("body", "{}"))
    logger.info("orchestrator_qa_complete", extra={"subject_id": subject_id, "status": body.get("status")})

    return {"subject_id": subject_id, "qa_status": body.get("status", "UNKNOWN")}


def invoke_canvas_publisher(event: dict, context: Any) -> dict:
    """Step 6: Invoke Canvas Publisher Lambda."""
    subject_id = event.get("subject_id") or event.get("qa", {}).get("subject_id", "")
    logger.info("orchestrator_canvas_start", extra={"subject_id": subject_id})

    lambda_client = boto3.client("lambda")
    canvas_function = os.environ.get("CANVAS_PUBLISHER_FUNCTION_NAME", "academic-pipeline-canvas-publisher-dev")

    response = lambda_client.invoke(
        FunctionName=canvas_function,
        InvocationType="RequestResponse",
        Payload=json.dumps({"subject_id": subject_id}),
    )

    result = json.loads(response["Payload"].read().decode("utf-8"))
    body = json.loads(result.get("body", "{}"))
    logger.info("orchestrator_canvas_complete", extra={"subject_id": subject_id})

    return {"subject_id": subject_id, "canvas_status": body.get("status", "UNKNOWN")}
