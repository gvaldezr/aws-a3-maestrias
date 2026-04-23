# Componentes Lógicos — U2: Agente Scholar

| Componente lógico | Servicio AWS | Config clave |
|---|---|---|
| Agente Scholar | Amazon Bedrock Agent | Model: Claude Sonnet 3.5, timeout: 300s, Action Group: ScopusActionGroup |
| Action Group Scopus | Lambda (Python 3.11) | timeout: 60s, memory: 256MB, env: SCOPUS_SECRET_ARN |
| Secreto Scopus | Secrets Manager | Heredado de U1 |
| Log Group | CloudWatch Logs | /academic-pipeline/{env}/u2, retención 90d |
| Métricas | CloudWatch Metrics | Namespace: AcademicPipeline/Scholar |
| Notificación escalación | SNS | Topic: academic-pipeline-staff-{env} |
