# Diseño de Infraestructura — U7: Interfaz Web

## Frontend
```
AWS Amplify Hosting (o S3 + CloudFront)
  ← React/Next.js build estático
  ← Cognito Hosted UI para login
  ← API Gateway como backend
```

## Backend Lambdas
```
Lambda: upload-handler          ← POST /api/upload (genera presigned URL)
Lambda: document-ingestion      ← S3 Event Trigger (parsea y dispara pipeline)
Lambda: dashboard-handler       ← GET /api/subjects
Lambda: checkpoint-get-handler  ← GET /api/subjects/{id}/checkpoint
```

## CDK Stack: WebInterfaceStack

```python
# Cognito User Pool
user_pool = cognito.UserPool(self, "StaffUserPool",
    user_pool_name=f"academic-pipeline-staff-{env_name}",
    self_sign_up_enabled=False,
    password_policy=cognito.PasswordPolicy(min_length=8, require_uppercase=True,
                                            require_digits=True, require_symbols=True),
    mfa=cognito.Mfa.OPTIONAL,
    mfa_second_factor=cognito.MfaSecondFactor(otp=True, sms=False),
    account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
)
user_pool_client = user_pool.add_client("WebClient",
    auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
    access_token_validity=Duration.hours(8),
)

# API Gateway con Cognito Authorizer
api = apigateway.RestApi(self, "PipelineAPI",
    rest_api_name=f"academic-pipeline-api-{env_name}",
    default_cors_preflight_options=apigateway.CorsOptions(
        allow_origins=[f"https://{amplify_domain}"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    ),
)
cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(self, "CognitoAuth",
    cognito_user_pools=[user_pool],
)

# Rutas API
upload_resource = api.root.add_resource("api").add_resource("upload")
upload_resource.add_method("POST", apigateway.LambdaIntegration(upload_lambda),
                            authorizer=cognito_authorizer)

subjects_resource = api.root.add_resource("api").add_resource("subjects")
subjects_resource.add_method("GET", apigateway.LambdaIntegration(dashboard_lambda),
                              authorizer=cognito_authorizer)

# S3 Event → document-ingestion Lambda
subjects_bucket.add_event_notification(
    s3.EventType.OBJECT_CREATED,
    s3n.LambdaDestination(ingestion_lambda),
    s3.NotificationKeyFilter(prefix="uploads/"),
)
```
