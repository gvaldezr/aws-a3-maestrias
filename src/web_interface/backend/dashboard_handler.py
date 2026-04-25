"""Dashboard Handler — GET /api/subjects."""
from __future__ import annotations

import json
import os
from typing import Any

import boto3


def lambda_handler(event: dict, context: Any) -> dict:
    try:
        ddb = boto3.resource("dynamodb")
        table = ddb.Table(os.environ.get("SUBJECTS_TABLE_NAME", "academic-pipeline-subjects-dev"))
        resp = table.scan(
            FilterExpression="SK = :sk",
            ExpressionAttributeValues={":sk": "STATE"},
            Limit=100,
        )
        subjects = []
        for item in resp.get("Items", []):
            subjects.append({
                "subject_id": item.get("subject_id", ""),
                "subject_name": item.get("subject_name", ""),
                "program_name": item.get("program_name", ""),
                "current_state": item.get("current_state", ""),
                "updated_at": item.get("updated_at", ""),
                "pending_approval": item.get("current_state") == "PENDING_APPROVAL",
            })

        pending = sum(1 for s in subjects if s["current_state"] == "PENDING_APPROVAL")
        published = sum(1 for s in subjects if s["current_state"] == "PUBLISHED")
        failed = sum(1 for s in subjects if "FAILED" in s["current_state"])

        return _resp(200, {
            "subjects": subjects,
            "total": len(subjects),
            "pending_approval_count": pending,
            "published_count": published,
            "failed_count": failed,
        })
    except Exception as e:
        return _resp(500, {"error": str(e)})


def _resp(code: int, body: dict) -> dict:
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization,Content-Type",
        },
        "body": json.dumps(body),
    }
