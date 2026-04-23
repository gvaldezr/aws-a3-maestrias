"""CDK Stack — Canvas Publisher (U6)."""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_sns as sns,
)
from constructs import Construct


class CanvasPublisherStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str,
                 subjects_bucket_name: str, subjects_table_name: str,
                 canvas_secret_arn: str, staff_topic_arn: str,
                 alerts_topic_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cdk.Tags.of(self).add("Project", "academic-pipeline")
        cdk.Tags.of(self).add("Unit", "u6-canvas-publisher")
        cdk.Tags.of(self).add("Environment", env_name)

        bucket = s3.Bucket.from_bucket_name(self, "Bucket", subjects_bucket_name)
        table = dynamodb.Table.from_table_name(self, "Table", subjects_table_name)
        canvas_secret = secretsmanager.Secret.from_secret_complete_arn(self, "CanvasSecret", canvas_secret_arn)
        staff_topic = sns.Topic.from_topic_arn(self, "StaffTopic", staff_topic_arn)
        alerts_topic = sns.Topic.from_topic_arn(self, "AlertsTopic", alerts_topic_arn)

        publisher_lambda = lambda_.Function(self, "CanvasPublisher",
            function_name=f"academic-pipeline-canvas-publisher-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="publisher.lambda_handler",
            code=lambda_.Code.from_asset("src/canvas_publisher"),
            timeout=cdk.Duration.seconds(300),
            memory_size=512,
            environment={
                "SUBJECTS_BUCKET_NAME": subjects_bucket_name,
                "SUBJECTS_TABLE_NAME": subjects_table_name,
                "CANVAS_SECRET_ARN": canvas_secret_arn,
                "CANVAS_BASE_URL": "https://institution.instructure.com",  # configurar por entorno
                "CANVAS_ACCOUNT_ID": "1",
                "STAFF_NOTIFICATIONS_TOPIC_ARN": staff_topic_arn,
                "PIPELINE_ALERTS_TOPIC_ARN": alerts_topic_arn,
            },
        )
        bucket.grant_read_write(publisher_lambda)
        table.grant_read_write_data(publisher_lambda)
        canvas_secret.grant_read(publisher_lambda)
        staff_topic.grant_publish(publisher_lambda)
        alerts_topic.grant_publish(publisher_lambda)

        cdk.CfnOutput(self, "CanvasPublisherArn", value=publisher_lambda.function_arn)
