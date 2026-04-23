# Arquitectura de Despliegue — U1: Infraestructura Base + JSON Schema

---

## Entornos

| Entorno | Cuenta AWS | Propósito |
|---|---|---|
| dev | cuenta-dev | Desarrollo y pruebas unitarias |
| staging | cuenta-staging | Pruebas de integración y contrato |
| prod | cuenta-prod | Producción |

## Secuencia de Despliegue

```
1. cdk bootstrap (una vez por cuenta/región)
2. cdk deploy InfrastructureBaseStack --context env=dev
3. Poblar secretos manualmente en Secrets Manager (Scopus API Key, Canvas Token)
4. Ejecutar tests de infraestructura (cdk synth + assertions)
5. Promover a staging → prod con aprobación manual
```

## Región AWS
`us-east-1` (primaria) — todos los recursos de U1 en la misma región para minimizar latencia entre S3, DynamoDB y los agentes Bedrock.

## Tagging obligatorio
Todos los recursos llevan:
```
Project: academic-pipeline
Unit: u1-infrastructure
Environment: dev|staging|prod
ManagedBy: cdk
```

## Diagrama de Recursos

```
VPC (private subnets)
  |
  +-- VPC Endpoint --> S3 Bucket (subjects, versionado, SSE-KMS)
  |
  +-- VPC Endpoint --> DynamoDB Table (subjects, On-Demand, GSI-1, GSI-2)
  |
  +-- KMS CMK (cifrado de S3 + DynamoDB + Secrets)
  |
  +-- Secrets Manager (scopus-api-key, canvas-oauth-token)
  |
  +-- SNS Topics (pipeline-alerts, staff-notifications, admin-alerts)
  |
  +-- CloudWatch Log Groups (/academic-pipeline/u1..u7, retención 90d)
  |
  +-- IAM Roles (1 por unidad, least-privilege)
```
