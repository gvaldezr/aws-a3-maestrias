---
inclusion: auto
---

# Convenciones de Código — Pipeline Académico

## Lenguaje y estilo

### Python (backend, agentes, lambdas, CDK)
- **Versión**: Python 3.11
- **Type hints**: Usar `from __future__ import annotations` en todos los módulos
- **Docstrings**: Triple-quoted, primera línea describe el propósito. Incluir Args/Returns cuando aplique.
- **Imports**: stdlib → terceros → locales, separados por línea en blanco
- **Naming**: `snake_case` para funciones/variables, `PascalCase` para clases, `UPPER_SNAKE` para constantes
- **Línea máxima**: 120 caracteres

### TypeScript (frontend)
- **Versión**: TypeScript 5.6+
- **Framework**: React 18 con Vite 6
- **Naming**: `camelCase` para variables/funciones, `PascalCase` para componentes/tipos

## Patrón de agentes (AgentCore + Strands SDK)

Todos los agentes siguen el mismo patrón. **No desviarse**:

```python
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext

app = BedrockAgentCoreApp()
_agent = None  # Lazy-initialized global

def _get_agent():
    """Lazy init — solo crear Strands Agent en primera invocación."""
    global _agent
    if _agent is not None:
        return _agent
    from strands import Agent, tool
    from strands.models import BedrockModel
    model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-6", ...)
    
    @tool
    def my_tool(...) -> dict:
        """Docstring con Args."""
        ...
    
    _agent = Agent(model=model, tools=[my_tool], system_prompt="...")
    return _agent

@app.entrypoint
def invoke(payload: dict, context: RequestContext = None) -> dict:
    """AgentCore Runtime entrypoint."""
    ...

if __name__ == "__main__":
    app.run()
```

### Reglas de agentes
- **Lazy init**: Los imports de `strands` van DENTRO de `_get_agent()`, nunca a nivel de módulo
- **Tools**: Definidos como funciones con `@tool` dentro de `_get_agent()`, retornan `dict`
- **`_ensure_dicts()`**: Siempre coercionar listas que pueden contener strings JSON a dicts
- **Self-persist**: Cada agente persiste sus resultados directamente a S3 + DynamoDB
- **State regression guard**: Verificar que el nuevo estado no retroceda (`advanced_states` check)
- **JSON output**: Los agentes retornan un bloque ```json con las claves esperadas

## Patrón de persistencia

### Subject JSON (S3)
- Bucket: `academic-pipeline-subjects-{account}-{region}-{env}`
- Key: `subjects/{subject_id}/subject.json`
- Versionado habilitado, cifrado SSE-KMS
- Cada agente lee → enriquece su sección → escribe de vuelta

### DynamoDB (índice de estado)
- Tabla: `academic-pipeline-subjects-{env}`
- PK: `subject_id`, SK: `STATE`
- GSI `state-index` para consultas por estado

## Logging estructurado

Usar `get_logger(__name__)` de `src/infrastructure/observability/logger.py`:
```python
from src.infrastructure.observability.logger import get_logger
logger = get_logger(__name__)
logger.info("operation_name", extra={"subject_id": sid, "key": "value"})
```

### Reglas de logging
- **JSON estructurado** siempre — nunca print() ni f-strings en logs
- **Redacción automática** de campos sensibles: password, token, api_key, secret, authorization
- **correlation_id** incluido automáticamente desde `CORRELATION_ID` env var
- **Nunca loguear**: secretos, tokens, PII, contenido completo de Subject JSON

## Manejo de errores

- APIs externas (Scopus, Canvas): backoff exponencial con máx. 3 reintentos
- Transiciones de estado: validar con `VALID_STATE_TRANSITIONS` antes de actualizar
- Schema validation: usar `validate_subject_json()` antes de persistir (excepto QA report y checkpoint que escriben directo)
- Escalación: notificar vía SNS cuando se agotan reintentos

## Secretos

- **Nunca** hardcodear secretos, tokens ni API keys en código
- Recuperar de Secrets Manager en runtime: `academic-pipeline/{env}/scopus-api-key`, `academic-pipeline/{env}/canvas-oauth-token`
- Variables de entorno para ARNs de secretos: `SCOPUS_SECRET_ARN`, `CANVAS_SECRET_ARN`

## CDK (IaC)

- Stacks en `src/infrastructure/stacks/`
- Naming: `{service}-{env}` (ej: `academic-pipeline-subjects-dev`)
- Cifrado KMS para S3 y DynamoDB
- IAM least-privilege por componente
- Tags obligatorios: `Project`, `Environment`, `Unit`
