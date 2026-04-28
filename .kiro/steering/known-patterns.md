---
inclusion: auto
---

# Patrones Conocidos y Lecciones Aprendidas

## Patrones que funcionan — NO cambiar

### 1. LLM individual calls (Content Agent)
El Content Agent NO usa el agent loop de Strands para generar contenido. Llama a las tools directamente para evitar `MaxTokensReachedException`. El agent loop solo se usa para inicializar las tools.

### 2. Self-persist en agentes
Cada agente persiste sus resultados directamente a S3 + DynamoDB al final de `invoke()`. No dependen del orquestador para persistir.

### 3. `_ensure_dicts()` para coerción
Los LLMs a veces pasan strings JSON donde se esperan dicts. Todas las tools usan `_ensure_dicts()` para coercionar.

### 4. OpenAlex como complemento de Scopus
La Scopus Abstract API retorna 401 con la API key actual. OpenAlex se usa para obtener abstracts gratuitos. El Scholar agent auto-enriquece papers con abstracts de OpenAlex durante el persist.

### 5. Direct S3 write para QA y Checkpoint
El QA report y las decisiones de checkpoint escriben directamente a S3 sin pasar por el schema validator, porque sus secciones tienen campos opcionales que el validator estricto rechaza.

### 6. Gateway Responses para CORS
API Gateway necesita Gateway Responses configuradas para 4xx/5xx además de los headers CORS en las respuestas Lambda. El frontend usa `IdToken` (no `AccessToken`) para autenticación.

### 7. 1 módulo por semana en Canvas
Canvas Publisher crea un módulo por semana + módulos globales (Información General, Reto Agéntico). Las rúbricas se renderizan como tablas HTML con colores (4 niveles).

## Problemas conocidos pendientes

| Problema | Severidad | Workaround |
|----------|-----------|-----------|
| Content agent ~5 min | Baja | Dentro del timeout de 900s |
| Scopus Abstract API 401 | Baja | OpenAlex como complemento |
| Test coverage 26% | Baja | 191 tests pasan |
| RF-09 Paralelo (1 asignatura a la vez) | Media | Falta Map state en Step Functions |
| RF-11 Alarmas SNS sin suscriptores | Baja | Topics existen pero sin suscriptores |

## Anti-patrones — NO hacer

1. **No usar agent loop para contenido largo** — causa MaxTokensReachedException
2. **No hardcodear secretos** — siempre Secrets Manager
3. **No loguear contenido completo de Subject JSON** — solo IDs y estados
4. **No retroceder estados** — verificar `advanced_states` antes de actualizar
5. **No usar `AccessToken` para API Gateway** — usar `IdToken` de Cognito
6. **No asumir que Scopus retorna abstracts** — siempre complementar con OpenAlex
7. **No sobreescribir audit.md completo** — siempre append
