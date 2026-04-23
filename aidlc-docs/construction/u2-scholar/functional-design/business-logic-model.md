# Modelo de Lógica de Negocio — U2: Agente Scholar

## Flujo Principal (Fases 1 y 2)

### generate_search_keywords(learning_outcomes, competencies) → list[str]
1. Extraer términos clave de cada RA (sustantivos y verbos técnicos)
2. Extraer términos clave de cada competencia
3. Combinar y deduplicar; priorizar términos de mayor especificidad
4. Retornar lista de 5–10 keywords ordenadas por relevancia estimada

### search_scopus(query: ScopusSearchQuery) → list[Paper]
1. Obtener API Key desde Secrets Manager (BR-S09)
2. Construir query Scopus: `TITLE-ABS-KEY({keywords}) AND SRCTITLE({journals}) AND PUBYEAR > {year}`
3. Ejecutar request con filtro Q1/Q2 y año mínimo 2019 (BR-S04)
4. Gestionar rate limiting: esperar 1s entre llamadas; backoff exponencial ante 429 (BR-S06)
5. Parsear respuesta y construir lista de `Paper`
6. Descartar papers sin cuartil definido (BR-S03)
7. Retornar lista cruda (sin límite de 20 aún)

### rank_and_select_top20(papers, learning_outcomes) → list[Paper]
1. Calcular `relevance_score` por paper:
   - Coincidencia de keywords en título: +0.4
   - Coincidencia de keywords en abstract: +0.3
   - Cuartil Q1: +0.2, Q2: +0.1
   - Recencia (año >= 2022): +0.1
2. Ordenar por `relevance_score` descendente
3. Retornar los primeros 20 (BR-S02)

### validate_corpus(papers, learning_outcomes) → CorpusValidation
1. Verificar que `len(papers) >= 5` (BR-S01)
2. Para cada RA, verificar que al menos 1 paper cubre su dominio temático
3. Retornar `CorpusValidation` con `is_sufficient` y lista de gaps

### extract_knowledge_matrix(papers, learning_outcomes) → list[KnowledgeMatrixEntry]
1. Para cada paper del Top 20:
   - Extraer concepto principal (via LLM prompt)
   - Identificar metodología aplicable
   - Generar aplicación ejecutiva con enfoque directivo
   - Mapear a RA relevantes
2. Verificar cobertura de todos los RA (BR-S08)
3. Retornar lista de `KnowledgeMatrixEntry`

### escalate_insufficient_corpus(subject_id, validation) → None
1. Actualizar estado JSON a `RESEARCH_ESCALATED`
2. Publicar mensaje SNS con: subject_id, keywords usadas, papers encontrados, gaps de RA
3. Registrar en CloudWatch con nivel WARNING
