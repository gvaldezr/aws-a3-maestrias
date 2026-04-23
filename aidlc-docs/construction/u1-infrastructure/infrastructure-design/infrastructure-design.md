# Diseño de Infraestructura — U1: Infraestructura Base + JSON Schema

---

## Stack CDK: `InfrastructureBaseStack`

**Archivo**: `src/infrastructure/stacks/infrastructure_base_stack.py`

### Recursos provisionados

#### KMS
```python
kms_key = kms.Key(self, "PipelineKey",
    enable_key_rotation=True,
    alias="alias/academic-pipeline",
    description="CMK para cifrado de S3, DynamoDB y Secrets Manager del pipeline"
)
```

#### S3 Bucket
```python
subjects_bucket = s3.Bucket(self, "SubjectsBucket",
    bucket_name=f"academic-pipeline-subjects-{account}-{region}",
    versioned=True,
    encryption=s3.BucketEncryption.KMS,
    encryption_key=kms_key,
    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
    enforce_ssl=True,
    lifecycle_rules=[
        s3.LifecycleRule(
            transitions=[s3.Transition(
                storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                transition_after=Duration.days(90)
            )]
        )
    ]
)
```

#### DynamoDB Table
```python
subjects_table = dynamodb.Table(self, "SubjectsTable",
    table_name="academic-pipeline-subjects",
    partition_key=dynamodb.Attribute(name="subject_id", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
    billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
    encryption_key=kms_key,
    point_in_time_recovery=True
)
# GSI-1: state-index
subjects_table.add_global_secondary_index(
    index_name="state-index",
    partition_key=dynamodb.Attribute(name="current_state", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="updated_at", type=dynamodb.AttributeType.STRING)
)
# GSI-2: program-index
subjects_table.add_global_secondary_index(
    index_name="program-index",
    partition_key=dynamodb.Attribute(name="program_name", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="updated_at", type=dynamodb.AttributeType.STRING)
)
```

#### Secrets Manager
```python
scopus_secret = secretsmanager.Secret(self, "ScopusApiKey",
    secret_name="academic-pipeline/scopus-api-key",
    description="API Key institucional de Scopus (Elsevier)"
)
canvas_secret = secretsmanager.Secret(self, "CanvasOAuthToken",
    secret_name="academic-pipeline/canvas-oauth-token",
    description="OAuth Token de Canvas LMS Cloud"
)
```

#### SNS Topics
```python
pipeline_alerts = sns.Topic(self, "PipelineAlerts", topic_name="academic-pipeline-alerts")
staff_notifications = sns.Topic(self, "StaffNotifications", topic_name="academic-pipeline-staff")
admin_alerts = sns.Topic(self, "AdminAlerts", topic_name="academic-pipeline-admin")
```

#### CloudWatch Log Groups (1 por unidad)
```python
for unit in ["u1", "u2", "u3", "u4", "u5", "u6", "u7"]:
    logs.LogGroup(self, f"LogGroup{unit.upper()}",
        log_group_name=f"/academic-pipeline/{unit}",
        retention=logs.RetentionDays.THREE_MONTHS
    )
```

#### VPC Endpoints
```python
vpc.add_gateway_endpoint("S3Endpoint", service=ec2.GatewayVpcEndpointAwsService.S3)
vpc.add_gateway_endpoint("DynamoDBEndpoint", service=ec2.GatewayVpcEndpointAwsService.DYNAMODB)
```

---

## Outputs del Stack (para consumo por otras unidades)

```python
CfnOutput(self, "SubjectsBucketName", value=subjects_bucket.bucket_name)
CfnOutput(self, "SubjectsTableName", value=subjects_table.table_name)
CfnOutput(self, "KmsKeyArn", value=kms_key.key_arn)
CfnOutput(self, "PipelineAlertsTopicArn", value=pipeline_alerts.topic_arn)
CfnOutput(self, "StaffNotificationsTopicArn", value=staff_notifications.topic_arn)
CfnOutput(self, "ScopusSecretArn", value=scopus_secret.secret_arn)
CfnOutput(self, "CanvasSecretArn", value=canvas_secret.secret_arn)
```
