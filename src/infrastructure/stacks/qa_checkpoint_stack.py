"""CDK Stack — QA Gate + Checkpoint Humano (U5)."""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_s3 as s3,
    aws_sns as sns,
)
from constructs import Construct


class QACheckpointStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str,
                 subjects_bucket_name: str, subjects_table_name: str,
                 staff_topic_arn: str, alerts_topic_arn: str,
                 kms_key_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cdk.Tags.of(self).add("Project", "academic-pipeline")
        cdk.Tags.of(self).add("Unit", "u5-qa-checkpoint")
        cdk.Tags.of(self).add("Environment", env_name)

        # Shared layer with src.infrastructure modules
        shared_layer = lambda_.LayerVersion(self, "SharedLayer",
            code=lambda_.Code.from_asset("lambda-layer"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Shared infrastructure modules (logger, state_manager, schema)",
        )

        bucket = s3.Bucket.from_bucket_name(self, "Bucket", subjects_bucket_name)
        table = dynamodb.Table.from_table_name(self, "Table", subjects_table_name)
        staff_topic = sns.Topic.from_topic_arn(self, "StaffTopic", staff_topic_arn)
        alerts_topic = sns.Topic.from_topic_arn(self, "AlertsTopic", alerts_topic_arn)

        # Cognito User Pool
        self.user_pool = cognito.UserPool(self, "StaffUserPool",
            user_pool_name=f"academic-pipeline-staff-{env_name}",
            self_sign_up_enabled=False,
            password_policy=cognito.PasswordPolicy(
                min_length=8, require_uppercase=True, require_digits=True, require_symbols=True,
            ),
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(otp=True, sms=False),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        self.user_pool_client = self.user_pool.add_client("WebClient",
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            access_token_validity=cdk.Duration.hours(8),
        )

        # Shared Lambda env
        lambda_env = {
            "SUBJECTS_BUCKET_NAME": subjects_bucket_name,
            "SUBJECTS_TABLE_NAME": subjects_table_name,
            "STAFF_NOTIFICATIONS_TOPIC_ARN": staff_topic_arn,
            "PIPELINE_ALERTS_TOPIC_ARN": alerts_topic_arn,
        }

        # QA Gate Lambda
        qa_lambda = lambda_.Function(self, "QAGateHandler",
            function_name=f"academic-pipeline-qa-gate-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="qa_gate.lambda_handler",
            code=lambda_.Code.from_asset("src/qa_checkpoint"),
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            environment=lambda_env,
            layers=[shared_layer],
        )
        bucket.grant_read_write(qa_lambda)
        table.grant_read_write_data(qa_lambda)
        staff_topic.grant_publish(qa_lambda)

        # Checkpoint Lambda
        checkpoint_lambda = lambda_.Function(self, "CheckpointHandler",
            function_name=f"academic-pipeline-checkpoint-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="checkpoint.lambda_handler",
            code=lambda_.Code.from_asset("src/qa_checkpoint"),
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            environment=lambda_env,
            layers=[shared_layer],
        )
        bucket.grant_read_write(checkpoint_lambda)
        table.grant_read_write_data(checkpoint_lambda)
        staff_topic.grant_publish(checkpoint_lambda)
        alerts_topic.grant_publish(checkpoint_lambda)

        # Timeout Checker Lambda
        timeout_lambda = lambda_.Function(self, "TimeoutChecker",
            function_name=f"academic-pipeline-timeout-{env_name}",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="timeout_checker.lambda_handler",
            code=lambda_.Code.from_asset("src/qa_checkpoint"),
            timeout=cdk.Duration.seconds(60),
            memory_size=256,
            environment=lambda_env,
            layers=[shared_layer],
        )
        bucket.grant_read(timeout_lambda)
        table.grant_read_data(timeout_lambda)
        staff_topic.grant_publish(timeout_lambda)

        # EventBridge Rule — every hour
        events.Rule(self, "TimeoutSchedule",
            rule_name=f"academic-pipeline-timeout-{env_name}",
            schedule=events.Schedule.rate(cdk.Duration.hours(1)),
            targets=[targets.LambdaFunction(timeout_lambda)],
        )

        # API Gateway
        api = apigateway.RestApi(self, "CheckpointAPI",
            rest_api_name=f"academic-pipeline-api-{env_name}",
        )
        authorizer = apigateway.CognitoUserPoolsAuthorizer(self, "CognitoAuth",
            cognito_user_pools=[self.user_pool],
        )

        subjects_res = api.root.add_resource("subjects")
        subject_res = subjects_res.add_resource("{subject_id}")
        decision_res = subject_res.add_resource("decision")
        decision_res.add_method("POST",
            apigateway.LambdaIntegration(checkpoint_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )
        checkpoint_res = subject_res.add_resource("checkpoint")
        checkpoint_res.add_method("GET",
            apigateway.LambdaIntegration(qa_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )
        subjects_res.add_method("GET",
            apigateway.LambdaIntegration(qa_lambda),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # Outputs
        cdk.CfnOutput(self, "ApiUrl", value=api.url)
        cdk.CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        cdk.CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
