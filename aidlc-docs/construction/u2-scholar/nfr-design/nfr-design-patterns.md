# Patrones NFR — U2: Agente Scholar

## Patrón: Retry con Backoff Exponencial (tenacity)
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((RateLimitError, ScopusAPIError)),
    reraise=True,
)
async def call_scopus_api(query): ...
```

## Patrón: Circuit Breaker (escalación tras 3 fallos)
Si los 3 reintentos fallan, se lanza `CorpusInsufficientError` que el agente captura para escalar al Staff. No se reintenta indefinidamente.

## Patrón: Idempotencia por subject_id
Antes de ejecutar la búsqueda, el agente verifica el estado actual del JSON. Si ya está en `KNOWLEDGE_MATRIX_READY`, retorna el resultado existente sin re-ejecutar.

## Patrón: Structured Logging sin secretos
Todas las llamadas a Scopus se loguean con: keywords (no la API Key), duración, código de respuesta y número de resultados. La API Key nunca aparece en logs (SECURITY-03).

## Patrón: Relevance Scoring determinista
El cálculo de `relevance_score` es una función pura (sin efectos secundarios) que permite PBT de invariantes (score siempre en [0.0, 1.0]).
