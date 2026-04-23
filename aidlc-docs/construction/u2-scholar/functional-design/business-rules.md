# Reglas de Negocio — U2: Agente Scholar

## BR-S01 — Mínimo de papers
El corpus debe contener al menos 5 papers Q1/Q2 relevantes. Si se recuperan menos, el agente escala antes de continuar.

## BR-S02 — Máximo Top 20
El listado final no puede superar 20 papers. Si Scopus retorna más, se rankean por relevance_score y se toman los 20 primeros.

## BR-S03 — Solo Q1/Q2
Solo se aceptan papers de revistas Q1 o Q2 según el cuartil de Scopus. Papers sin cuartil definido se descartan.

## BR-S04 — Recencia mínima
Los papers deben ser del año 2019 en adelante (últimos 5+ años). Papers anteriores solo se incluyen si no hay suficientes recientes.

## BR-S05 — Keywords derivadas de RA y competencias
Las keywords de búsqueda deben derivarse exclusivamente de los RA y competencias de la asignatura. No se usan keywords genéricas.

## BR-S06 — Rate limiting Scopus
Entre llamadas a la API de Scopus se respeta un intervalo mínimo de 1 segundo. Ante error 429, se aplica backoff exponencial (1s, 2s, 4s) con máximo 3 reintentos.

## BR-S07 — Escalación por corpus insuficiente
Si tras 3 intentos de búsqueda con keywords distintas el corpus sigue siendo insuficiente (< 5 papers), el agente marca el JSON con estado `RESEARCH_ESCALATED` y notifica al Staff vía SNS. El pipeline se detiene para esa asignatura.

## BR-S08 — Matriz de Conocimiento cubre todos los RA
La Matriz de Conocimiento debe tener al menos una entrada con `ra_relevance` para cada RA de la asignatura. Si algún RA queda sin cobertura, se registra como gap en `CorpusValidation`.

## BR-S09 — Credenciales desde Secrets Manager
La API Key de Scopus se obtiene exclusivamente desde AWS Secrets Manager en tiempo de ejecución. Nunca se hardcodea ni se pasa como variable de entorno.
