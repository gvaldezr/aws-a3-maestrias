"""CDK Stack — Web Interface (U7): Upload + Ingestion + Dashboard."""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_sns as sns,
)
from constructs import Construct


class WebInterfaceStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str,
                 subjects_bucket_name: str, subjects_table_name: str,
                 staff_topic_arn: str, user_pool_id: str, user_pool_client_id: str,
                 api_url: str, scholar_runtime_arn: str = "",
                 kms_key_arn: str = "", state_machine_arn: str = "", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cdk.Tags.of(self).add("Project", "academic-pipeline")
        cdk.Tags.of(self).add("Unit", "u7-web-interface")
        cdk.Tags.of(self).add("Environment", env_name)

        bucket = s3.Bucket.from_bucket_name(self, "Bucket", subjects_bucket_name)
        table = dynamodb.Table.from_table_name(self, "Table", subjects_table_name)

        # KMS key for encrypted S3/DynamoDB access
        from aws_cdk import aws_kms as kms, aws_iam as iam
        if kms_key_arn:
            encryption_key = kms.Key.from_key_arn(self, "KmsKey", kms_key_arn)

        # Shared layer
        shared_layer = lambda_.LayerVersion(self, "SharedLayer",
            code=lambda_.Code.from_asset("lambda-layer"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Shared infrastructure modules",
        )

        lambda_env = {
            "SUBJECTS_BUCKET_NAME": subjects_bucket_name,
            "SUBJECTS_TABLE_NAME": subjects_table_name,
            "SCHOLAR_AGENT_RUNTIME_ARN": scholar_runtime_arn,
            "STAFF_NOTIFICATIONS_TOPIC_ARN": staff_topic_arn,
            "ALLOWED_ORIGIN": f"https://pipeline-{env_name}.example.com",
            "STATE_MACHINE_ARN": state_machine_arn,
        }

        # Upload Handler
        upload_lambda = lambda_.Function(self, "UploadHandler",
            function_name=f"academic-pipeline-upload-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="upload_handler.lambda_handler",
            code=lambda_.Code.from_asset("src/web_interface/backend"),
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            environment=lambda_env,
            layers=[shared_layer],
        )
        bucket.grant_put(upload_lambda)

        # Document Ingestion Handler (S3 trigger)
        ingestion_lambda = lambda_.Function(self, "IngestionHandler",
            function_name=f"academic-pipeline-ingestion-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="ingestion_handler.lambda_handler",
            code=lambda_.Code.from_asset("src/web_interface/backend"),
            timeout=cdk.Duration.seconds(120),
            memory_size=512,
            environment=lambda_env,
            layers=[shared_layer],
        )
        bucket.grant_read_write(ingestion_lambda)
        table.grant_read_write_data(ingestion_lambda)

        # S3 Event → Ingestion Lambda (uploads/ prefix)
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(ingestion_lambda),
            s3.NotificationKeyFilter(prefix="uploads/"),
        )

        # Dashboard Handler
        dashboard_lambda = lambda_.Function(self, "DashboardHandler",
            function_name=f"academic-pipeline-dashboard-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="dashboard_handler.lambda_handler",
            code=lambda_.Code.from_asset("src/web_interface/backend"),
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            environment=lambda_env,
            layers=[shared_layer],
        )
        table.grant_read_data(dashboard_lambda)

        # API Gateway (reuse from U5 or create new)
        api = apigateway.RestApi(self, "WebAPI",
            rest_api_name=f"academic-pipeline-web-{env_name}",
        )
        user_pool = cognito.UserPool.from_user_pool_id(self, "UserPool", user_pool_id)
        authorizer = apigateway.CognitoUserPoolsAuthorizer(self, "WebAuth",
            cognito_user_pools=[user_pool],
        )

        api_res = api.root.add_resource("api")
        upload_res = api_res.add_resource("upload")
        upload_res.add_method("POST",
            apigateway.LambdaIntegration(upload_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )
        subjects_res = api_res.add_resource("subjects")
        subjects_res.add_method("GET",
            apigateway.LambdaIntegration(dashboard_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        cdk.CfnOutput(self, "WebApiUrl", value=api.url)
        cdk.CfnOutput(self, "UploadLambdaArn", value=upload_lambda.function_arn)
        cdk.CfnOutput(self, "IngestionLambdaArn", value=ingestion_lambda.function_arn)

        # KMS grants (after all lambdas are defined)
        if kms_key_arn:
            encryption_key.grant_encrypt_decrypt(upload_lambda)
            encryption_key.grant_encrypt_decrypt(ingestion_lambda)
            encryption_key.grant_encrypt_decrypt(dashboard_lambda)

        # Grant Step Functions start execution
        state_machine_arn = lambda_env.get("STATE_MACHINE_ARN", "")
        if state_machine_arn:
            ingestion_lambda.add_to_role_policy(iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[state_machine_arn],
            ))
