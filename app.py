#!/usr/bin/env python3
"""CDK App entry point — Academic Pipeline."""
import aws_cdk as cdk
from src.infrastructure.stacks.infrastructure_base_stack import InfrastructureBaseStack
from src.infrastructure.stacks.qa_checkpoint_stack import QACheckpointStack
from src.infrastructure.stacks.canvas_publisher_stack import CanvasPublisherStack
from src.infrastructure.stacks.web_interface_stack import WebInterfaceStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "dev"
account = app.node.try_get_context("account") or "254508868459"
region = app.node.try_get_context("region") or "us-east-1"
aws_env = cdk.Environment(account=account, region=region)

# ── U1: Infraestructura Base ─────────────────────────────────────────────────
infra = InfrastructureBaseStack(
    app, f"AcademicPipeline-Infrastructure-{env_name.capitalize()}",
    env_name=env_name, env=aws_env,
    description="Academic Pipeline — Infraestructura Base + JSON Schema",
)

# Shared resource names (from U1 outputs)
bucket_name = infra.subjects_bucket.bucket_name
table_name = infra.subjects_table.table_name
kms_arn = infra.kms_key.key_arn
staff_topic_arn = infra.staff_notifications_topic.topic_arn
alerts_topic_arn = infra.pipeline_alerts_topic.topic_arn
canvas_secret_arn = infra.canvas_secret.secret_arn

# ── U5: QA Gate + Checkpoint Humano ──────────────────────────────────────────
qa_stack = QACheckpointStack(
    app, f"AcademicPipeline-QACheckpoint-{env_name.capitalize()}",
    env_name=env_name, env=aws_env,
    subjects_bucket_name=bucket_name,
    subjects_table_name=table_name,
    staff_topic_arn=staff_topic_arn,
    alerts_topic_arn=alerts_topic_arn,
    kms_key_arn=kms_arn,
    description="Academic Pipeline — QA Gate + Checkpoint Humano",
)
qa_stack.add_dependency(infra)

# ── U6: Canvas Publisher ─────────────────────────────────────────────────────
canvas_stack = CanvasPublisherStack(
    app, f"AcademicPipeline-CanvasPublisher-{env_name.capitalize()}",
    env_name=env_name, env=aws_env,
    subjects_bucket_name=bucket_name,
    subjects_table_name=table_name,
    canvas_secret_arn=canvas_secret_arn,
    staff_topic_arn=staff_topic_arn,
    alerts_topic_arn=alerts_topic_arn,
    description="Academic Pipeline — Canvas LMS Publisher",
)
canvas_stack.add_dependency(infra)

# ── U7: Web Interface ────────────────────────────────────────────────────────
web_stack = WebInterfaceStack(
    app, f"AcademicPipeline-WebInterface-{env_name.capitalize()}",
    env_name=env_name, env=aws_env,
    subjects_bucket_name=bucket_name,
    subjects_table_name=table_name,
    staff_topic_arn=staff_topic_arn,
    user_pool_id=qa_stack.user_pool.user_pool_id,
    user_pool_client_id=qa_stack.user_pool_client.user_pool_client_id,
    api_url="",  # se resuelve post-deploy
    scholar_runtime_arn="arn:aws:bedrock-agentcore:us-east-1:254508868459:runtime/AcademicPipelineScholarDev-7S4W3RBBi0",
    description="Academic Pipeline — Web Interface + Document Ingestion",
)
web_stack.add_dependency(qa_stack)

app.synth()
