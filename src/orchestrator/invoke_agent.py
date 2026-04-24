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
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
import urllib.request
import urllib.error

from src.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

SCHOLAR_ARN = os.environ.get("SCHOLAR_RUNTIME_ARN", "")
DI_ARN = os.environ.get("DI_RUNTIME_ARN", "")
CONTENT_ARN = os.environ.get("CONTENT_RUNTIME_ARN", "")


def _invoke_runtime(runtime_arn: str, payload: dict) -> dict:
    """Invoke AgentCore Runtime via signed HTTP request."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    runtime_id = runtime_arn.split("/")[-1]
    session_id = f"orch-{uuid.uuid4().hex[:16]}"

    # Build the invoke URL
    url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{runtime_id}/endpoints/DEFAULT/sessions/{session_id}/invocations"

    body = json.dumps(payload).encode("utf-8")

    # Sign the request with SigV4
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    request = AWSRequest(method="POST", url=url, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    SigV4Auth(credentials, "bedrock-agentcore", region).add_auth(request)

    req = urllib.request.Request(
        url=url,
        data=body,
        headers=dict(request.headers),
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        logger.error("agentcore_invoke_failed", extra={"runtime_id": runtime_id, "status": e.code, "error": error_body[:200]})
        return {"error": error_body[:500], "status_code": e.code}
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
