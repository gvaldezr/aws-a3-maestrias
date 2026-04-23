# Performance Test Instructions
## Pipeline Académico → Canvas LMS

---

## Requerimientos de Rendimiento

| Componente | Métrica | Target |
|---|---|---|
| Agente Scholar | Tiempo por asignatura | < 5 min |
| Agente DI | Tiempo por asignatura | < 4 min |
| Agente Content | Tiempo por asignatura (con Maestría) | < 8 min |
| QA Gate Lambda | Tiempo de validación | < 30s |
| Canvas Publisher Lambda | Tiempo de publicación | < 5 min |
| Dashboard API | Latencia p99 | < 500ms |
| Pipeline completo | Tiempo extremo a extremo | < 30 min |
| Paralelismo | Asignaturas simultáneas | 20 sin degradación |

---

## Herramienta: Locust (carga en API Gateway)

```bash
pip install locust

# Ejecutar test de carga en Dashboard API
locust -f tests/performance/locustfile.py \
  --host=${API_GATEWAY_URL} \
  --users=20 \
  --spawn-rate=2 \
  --run-time=5m \
  --headless \
  --csv=performance-results/dashboard-load
```

### locustfile.py (Dashboard API)

```python
from locust import HttpUser, task, between

class StaffUser(HttpUser):
    wait_time = between(5, 15)

    @task
    def get_dashboard(self):
        self.client.get(
            "/api/subjects",
            headers={"Authorization": f"Bearer {TEST_JWT_TOKEN}"},
        )
```

---

## Test de Paralelismo (20 asignaturas simultáneas)

```bash
# Invocar 20 ejecuciones paralelas del pipeline con datos de prueba
python tests/performance/parallel_pipeline_test.py --subjects=20 --env=staging
```

**Verificar**:
- Ninguna ejecución falla por concurrencia
- DynamoDB no tiene ThrottledRequests
- S3 no tiene errores de escritura concurrente
- Tiempo total < 30 minutos para las 20 asignaturas

---

## Monitoreo Durante Tests

```bash
# CloudWatch métricas en tiempo real
aws cloudwatch get-metric-statistics \
  --namespace AcademicPipeline \
  --metric-name CoursesPublished \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Sum

# Verificar ThrottledRequests en DynamoDB
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ThrottledRequests \
  --dimensions Name=TableName,Value=academic-pipeline-subjects-dev \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Sum
```

---

## Criterios de Aceptación

- ✅ 20 asignaturas procesadas en paralelo sin errores de concurrencia
- ✅ DynamoDB ThrottledRequests = 0 durante el test
- ✅ Dashboard API latencia p99 < 500ms bajo 20 usuarios concurrentes
- ✅ Ningún agente excede su timeout configurado
