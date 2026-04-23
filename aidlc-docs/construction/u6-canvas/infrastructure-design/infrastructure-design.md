# Diseño de Infraestructura — U6: Publicación Canvas LMS

## Componentes AWS

```
Lambda: canvas-publisher-handler   ← invocado por orquestador tras APPROVED
Secrets Manager: canvas-oauth-token ← heredado de U1
S3: subjects-bucket                 ← heredado de U1
DynamoDB: subjects-table            ← heredado de U1
SNS: pipeline-alerts                ← heredado de U1
```

## CDK Stack: CanvasPublisherStack

```python
canvas_lambda = lambda_.Function(self, "CanvasPublisher",
    function_name=f"academic-pipeline-canvas-publisher-{env_name}",
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler="publisher.lambda_handler",
    code=lambda_.Code.from_asset("src/canvas-publisher"),
    timeout=Duration.seconds(300),
    memory_size=512,
    environment={
        "CANVAS_SECRET_ARN": canvas_secret_arn,
        "CANVAS_BASE_URL": canvas_base_url,   # ej: https://institution.instructure.com
        "SUBJECTS_BUCKET_NAME": subjects_bucket_name,
        "SUBJECTS_TABLE_NAME": subjects_table_name,
        "PIPELINE_ALERTS_TOPIC_ARN": pipeline_alerts_arn,
    },
)
canvas_secret.grant_read(canvas_lambda)
subjects_bucket.grant_read_write(canvas_lambda)
subjects_table.grant_read_write_data(canvas_lambda)
```

## Outputs
```python
CfnOutput(self, "CanvasPublisherArn", value=canvas_lambda.function_arn)
```
