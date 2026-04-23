# Diseño de Infraestructura — U5: QA Gate + Checkpoint Humano

## Componentes AWS

```
Lambda: qa-gate-handler          ← ejecuta run_qa_gate, notifica Staff
Lambda: checkpoint-handler       ← procesa decisiones del Staff (API Gateway)
Lambda: timeout-checker          ← invocado por EventBridge Scheduler cada hora
EventBridge Scheduler            ← dispara timeout-checker cada hora
API Gateway                      ← POST /subjects/{id}/decision (autenticado con Cognito JWT)
SNS Topic: staff-notifications   ← heredado de U1
DynamoDB: subjects-table         ← heredado de U1
S3: subjects-bucket              ← heredado de U1
```

## CDK Stack: QACheckpointStack

```python
# Lambda QA Gate
qa_lambda = lambda_.Function(self, "QAGateHandler",
    function_name=f"academic-pipeline-qa-gate-{env_name}",
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler="qa_gate.lambda_handler",
    code=lambda_.Code.from_asset("src/qa-checkpoint"),
    timeout=Duration.seconds(30),
    memory_size=256,
)

# Lambda Checkpoint (decisiones del Staff)
checkpoint_lambda = lambda_.Function(self, "CheckpointHandler",
    function_name=f"academic-pipeline-checkpoint-{env_name}",
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler="checkpoint.lambda_handler",
    code=lambda_.Code.from_asset("src/qa-checkpoint"),
    timeout=Duration.seconds(30),
    memory_size=256,
)

# Lambda Timeout Checker
timeout_lambda = lambda_.Function(self, "TimeoutChecker",
    function_name=f"academic-pipeline-timeout-{env_name}",
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler="timeout_checker.lambda_handler",
    code=lambda_.Code.from_asset("src/qa-checkpoint"),
    timeout=Duration.seconds(60),
)

# EventBridge Scheduler — cada hora
scheduler.CfnSchedule(self, "TimeoutSchedule",
    schedule_expression="rate(1 hour)",
    target=scheduler.CfnSchedule.TargetProperty(
        arn=timeout_lambda.function_arn,
        role_arn=scheduler_role.role_arn,
    ),
)

# API Gateway — POST /subjects/{id}/decision
api = apigateway.RestApi(self, "CheckpointAPI",
    rest_api_name=f"academic-pipeline-checkpoint-{env_name}",
    default_cors_preflight_options=apigateway.CorsOptions(
        allow_origins=["https://pipeline.example.com"],  # dominio de la interfaz web
        allow_methods=["POST", "GET"],
    ),
)
subjects = api.root.add_resource("subjects")
subject = subjects.add_resource("{subject_id}")
decision = subject.add_resource("decision")
decision.add_method("POST",
    apigateway.LambdaIntegration(checkpoint_lambda),
    authorizer=cognito_authorizer,  # JWT Cognito
)
```
