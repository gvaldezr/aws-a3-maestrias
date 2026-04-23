# Componentes Lógicos de Infraestructura — U1

| Componente lógico | Servicio AWS | Configuración clave |
|---|---|---|
| Almacén de JSON | S3 Bucket | Versionado ON, SSE-KMS, Block Public Access, lifecycle: mover a IA tras 90 días |
| Índice de estado | DynamoDB Table | On-Demand, SSE-KMS, GSI-1 (state-index), GSI-2 (program-index), TTL: no aplica |
| Bóveda de secretos | Secrets Manager | Rotación automática habilitada, 2 secretos: scopus-api-key, canvas-oauth-token |
| Clave de cifrado | KMS CMK | Rotación anual, política restringida a roles del pipeline |
| Bus de notificaciones | SNS Topics | 3 topics: pipeline-alerts, staff-notifications, admin-alerts |
| Registro de logs | CloudWatch Log Groups | Retención 90 días, 1 grupo por unidad: /pipeline/u1, /pipeline/u2, etc. |
| Endpoints privados | VPC Endpoints | S3 Gateway Endpoint, DynamoDB Gateway Endpoint |
| Roles IAM | IAM Roles | 1 rol por unidad, least-privilege, trust policy restringida a Lambda/Bedrock |
