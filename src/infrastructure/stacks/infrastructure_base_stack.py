"""CDK Stack — InfrastructureBaseStack (U1)."""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_kms as kms,
    aws_logs as logs,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_sns as sns,
)
from constructs import Construct


class InfrastructureBaseStack(cdk.Stack):
    """
    Provisiona todos los recursos base del pipeline académico:
    KMS, S3, DynamoDB, Secrets Manager, SNS, CloudWatch Log Groups, IAM Roles.
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = {
            "Project": "academic-pipeline",
            "Unit": "u1-infrastructure",
            "Environment": env_name,
            "ManagedBy": "cdk",
        }
        for key, value in tags.items():
            cdk.Tags.of(self).add(key, value)

        # ── KMS ──────────────────────────────────────────────────────────────
        self.kms_key = kms.Key(
            self, "PipelineKey",
            enable_key_rotation=True,
            alias=f"alias/academic-pipeline-{env_name}",
            description="CMK para cifrado de S3, DynamoDB y Secrets Manager",
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        # ── S3 ───────────────────────────────────────────────────────────────
        self.subjects_bucket = s3.Bucket(
            self, "SubjectsBucket",
            bucket_name=f"academic-pipeline-subjects-{self.account}-{self.region}-{env_name}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=cdk.Duration.days(90),
                        )
                    ]
                )
            ],
        )

        # ── DynamoDB ─────────────────────────────────────────────────────────
        self.subjects_table = dynamodb.Table(
            self, "SubjectsTable",
            table_name=f"academic-pipeline-subjects-{env_name}",
            partition_key=dynamodb.Attribute(name="subject_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        self.subjects_table.add_global_secondary_index(
            index_name="state-index",
            partition_key=dynamodb.Attribute(name="current_state", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="updated_at", type=dynamodb.AttributeType.STRING),
        )
        self.subjects_table.add_global_secondary_index(
            index_name="program-index",
            partition_key=dynamodb.Attribute(name="program_name", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="updated_at", type=dynamodb.AttributeType.STRING),
        )

        # ── Secrets Manager ──────────────────────────────────────────────────
        self.scopus_secret = secretsmanager.Secret(
            self, "ScopusApiKey",
            secret_name=f"academic-pipeline/{env_name}/scopus-api-key",
            description="API Key institucional de Scopus (Elsevier) — poblar manualmente",
            encryption_key=self.kms_key,
        )
        self.canvas_secret = secretsmanager.Secret(
            self, "CanvasOAuthToken",
            secret_name=f"academic-pipeline/{env_name}/canvas-oauth-token",
            description="OAuth Token de Canvas LMS Cloud — poblar manualmente",
            encryption_key=self.kms_key,
        )

        # ── SNS Topics ───────────────────────────────────────────────────────
        self.pipeline_alerts_topic = sns.Topic(
            self, "PipelineAlerts",
            topic_name=f"academic-pipeline-alerts-{env_name}",
            master_key=self.kms_key,
        )
        self.staff_notifications_topic = sns.Topic(
            self, "StaffNotifications",
            topic_name=f"academic-pipeline-staff-{env_name}",
            master_key=self.kms_key,
        )
        self.admin_alerts_topic = sns.Topic(
            self, "AdminAlerts",
            topic_name=f"academic-pipeline-admin-{env_name}",
            master_key=self.kms_key,
        )

        # ── CloudWatch Log Groups (1 por unidad, retención 90 días) ──────────
        for unit in ["u1", "u2", "u3", "u4", "u5", "u6", "u7"]:
            logs.LogGroup(
                self, f"LogGroup{unit.upper()}",
                log_group_name=f"/academic-pipeline/{env_name}/{unit}",
                retention=logs.RetentionDays.THREE_MONTHS,
                removal_policy=cdk.RemovalPolicy.RETAIN,
            )

        # ── IAM Roles base (least-privilege por unidad) ───────────────────────
        self._create_unit_roles(env_name)

        # ── Outputs ──────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "SubjectsBucketName", value=self.subjects_bucket.bucket_name)
        cdk.CfnOutput(self, "SubjectsTableName", value=self.subjects_table.table_name)
        cdk.CfnOutput(self, "KmsKeyArn", value=self.kms_key.key_arn)
        cdk.CfnOutput(self, "PipelineAlertsTopicArn", value=self.pipeline_alerts_topic.topic_arn)
        cdk.CfnOutput(self, "StaffNotificationsTopicArn", value=self.staff_notifications_topic.topic_arn)
        cdk.CfnOutput(self, "ScopusSecretArn", value=self.scopus_secret.secret_arn)
        cdk.CfnOutput(self, "CanvasSecretArn", value=self.canvas_secret.secret_arn)

    def _create_unit_roles(self, env_name: str) -> None:
        """Crea roles IAM con least-privilege para cada unidad del pipeline."""
        # Rol base para agentes Bedrock (U2, U3, U4)
        bedrock_agent_role = iam.Role(
            self, "BedrockAgentRole",
            role_name=f"academic-pipeline-bedrock-agent-{env_name}",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Rol para agentes Bedrock del pipeline académico",
        )
        self.subjects_bucket.grant_read_write(bedrock_agent_role)
        self.subjects_table.grant_read_write_data(bedrock_agent_role)
        self.kms_key.grant_encrypt_decrypt(bedrock_agent_role)

        # Rol para Lambdas de integración (U5, U6, U7)
        lambda_role = iam.Role(
            self, "PipelineLambdaRole",
            role_name=f"academic-pipeline-lambda-{env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Rol para Lambdas del pipeline académico",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )
        self.subjects_bucket.grant_read_write(lambda_role)
        self.subjects_table.grant_read_write_data(lambda_role)
        self.kms_key.grant_encrypt_decrypt(lambda_role)
        self.scopus_secret.grant_read(lambda_role)
        self.canvas_secret.grant_read(lambda_role)
        self.pipeline_alerts_topic.grant_publish(lambda_role)
        self.staff_notifications_topic.grant_publish(lambda_role)
