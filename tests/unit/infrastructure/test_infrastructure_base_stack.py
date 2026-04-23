"""Tests de CDK assertions para InfrastructureBaseStack — U1."""
from __future__ import annotations

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from src.infrastructure.stacks.infrastructure_base_stack import InfrastructureBaseStack


@pytest.fixture(scope="module")
def template() -> Template:
    app = cdk.App()
    stack = InfrastructureBaseStack(
        app, "TestStack",
        env_name="test",
        env=cdk.Environment(account="123456789012", region="us-east-1"),
    )
    return Template.from_stack(stack)


class TestInfrastructureBaseStack:
    def test_s3_bucket_has_versioning(self, template: Template):
        template.has_resource_properties("AWS::S3::Bucket", {
            "VersioningConfiguration": {"Status": "Enabled"},
        })

    def test_s3_bucket_blocks_public_access(self, template: Template):
        template.has_resource_properties("AWS::S3::Bucket", {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        })

    def test_dynamodb_table_is_pay_per_request(self, template: Template):
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "BillingMode": "PAY_PER_REQUEST",
        })

    def test_dynamodb_has_point_in_time_recovery(self, template: Template):
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "PointInTimeRecoverySpecification": {"PointInTimeRecoveryEnabled": True},
        })

    def test_kms_key_has_rotation_enabled(self, template: Template):
        template.has_resource_properties("AWS::KMS::Key", {
            "EnableKeyRotation": True,
        })

    def test_sns_topics_created(self, template: Template):
        template.resource_count_is("AWS::SNS::Topic", 3)

    def test_log_groups_created_for_all_units(self, template: Template):
        # 7 unidades = 7 log groups
        template.resource_count_is("AWS::Logs::LogGroup", 7)

    def test_log_groups_have_90_day_retention(self, template: Template):
        template.has_resource_properties("AWS::Logs::LogGroup", {
            "RetentionInDays": 90,
        })

    def test_secrets_manager_secrets_created(self, template: Template):
        template.resource_count_is("AWS::SecretsManager::Secret", 2)

    def test_iam_roles_created(self, template: Template):
        # Al menos 2 roles: bedrock-agent y lambda
        roles = template.find_resources("AWS::IAM::Role")
        assert len(roles) >= 2
