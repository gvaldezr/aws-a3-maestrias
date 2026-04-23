"""Métricas y notificaciones — ObservabilityComponent (C10)."""
from __future__ import annotations

import os

import boto3
from botocore.config import Config

_RETRY_CONFIG = Config(retries={"max_attempts": 3, "mode": "adaptive"})


def record_metric(metric_name: str, value: float, unit: str = "Count", dimensions: dict | None = None) -> None:
    """Publica una métrica en CloudWatch Metrics."""
    cw = boto3.client("cloudwatch", config=_RETRY_CONFIG)
    dim_list = [{"Name": k, "Value": v} for k, v in (dimensions or {}).items()]
    cw.put_metric_data(
        Namespace="AcademicPipeline",
        MetricData=[{
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Dimensions": dim_list,
        }],
    )


def send_notification(topic_arn: str, subject: str, message: str) -> None:
    """Envía una notificación vía SNS. No incluye secretos ni PII en el mensaje."""
    sns = boto3.client("sns", config=_RETRY_CONFIG)
    sns.publish(TopicArn=topic_arn, Subject=subject[:100], Message=message)
