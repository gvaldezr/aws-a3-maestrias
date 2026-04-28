# Known Issues — Pipeline Académico → Canvas LMS

## Resueltos

1. **Agentes sin contexto académico** → Cada agente carga subject JSON de S3
2. **MaxTokensReachedException** → Content agent usa llamadas LLM individuales (no agent loop)
3. **Auto-persistencia fallaba** → IAM permissions + direct persist + state regression guard
4. **DOCX parser no leía tablas** → Extrae tablas Anáhuac (nombre, RAs, syllabus, semanas)
5. **CORS en API Gateway** → Gateway Responses para 4xx/5xx + IdToken
6. **QA Report no persistía** → Direct S3 write (bypass schema validator)
7. **Semanas incorrectas** → Parser extrae "Duración del ciclo: N semanas"
8. **TypeError en tools** → `_ensure_dicts()` para strings JSON
9. **Contenido genérico** → Templates Anáhuac MADTFIN + LLM individual calls
10. **Scopus sin abstracts** → OpenAlex como complemento (auto-enrich en Scholar persist)
11. **Quiz formato incorrecto** → QA Gate acepta ra_ids (plural)
12. **Checkpoint 500 error** → Direct S3 write para approve/reject (bypass schema validator)
13. **Canvas un solo módulo** → 1 módulo por semana + módulos globales
14. **Rúbricas sin formato** → HTML tables con colores (4 niveles)
15. **Guía facilitador como JSON** → Renderizada como tabla HTML
16. **Reto en módulo incorrecto** → Módulo propio al final
17. **Nombre del curso genérico** → Usa nombre de la asignatura + prefijo MADTFIN

## Pendientes

| Problema | Severidad | Detalle |
|----------|-----------|---------|
| Content agent ~5 min con LLM | Baja | Dentro del timeout de 900s |
| Scopus Abstract API 401 | Baja | API key sin acceso. OpenAlex como complemento |
| Test coverage 26% | Baja | 191 tests pasan |
| RF-09 Paralelo | Media | 1 asignatura a la vez. Falta Map state en Step Functions |
| RF-11 Alarmas SNS | Baja | Topics existen pero sin suscriptores |
