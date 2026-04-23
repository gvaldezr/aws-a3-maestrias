# Modelo de Lógica de Negocio — U3: Agente DI

## structure_by_subject_type(knowledge_matrix, subject_type) → StructuredContent
1. Seleccionar nivel Bloom predominante según BR-DI04
2. Agrupar entradas de la Matriz de Conocimiento por afinidad temática
3. Asignar cada grupo a una semana del mapa (semana 1: Ingesta, semana 4: Síntesis)
4. Retornar contenido estructurado con nivel Bloom por semana

## generate_learning_objectives(structured_content, competencies, learning_outcomes) → list[LearningObjective]
1. Para cada RA, generar 1–3 objetivos usando verbos Bloom del nivel apropiado (BR-DI01, BR-DI04)
2. Para cada objetivo, buscar competencias del programa que lo cubran por afinidad semántica (BR-DI02)
3. Si no hay competencia para un objetivo → registrar AlignmentGap
4. Asignar objective_id único (formato: OBJ-{subject_id[:8]}-{n:03d})
5. Retornar lista de LearningObjective

## detect_alignment_gaps(objectives, competencies) → list[AlignmentGap]
1. Filtrar objetivos con `competency_ids` vacío
2. Para cada uno, construir AlignmentGap con ra_ids y reason
3. Retornar lista (vacía si no hay gaps)

## build_traceability_matrix(objectives, learning_outcomes) → list[TraceabilityEntry]
1. Para cada objetivo, para cada ra_id en objective.ra_ids:
   - Crear TraceabilityEntry(objective_id, bloom_level, competency_ids, ra_id)
2. Verificar que todos los RA tienen al menos una entrada (BR-DI03, BR-DI07)
3. Retornar matriz completa

## validate_ra_coverage(objectives, learning_outcomes) → list[str]
1. Recopilar todos los ra_ids cubiertos por los objetivos
2. Comparar con la lista completa de RA de la asignatura
3. Retornar lista de ra_ids sin cobertura (vacía si cobertura 100%)

## draft_descriptive_card(content_map, objectives, subject_json) → DescriptiveCard
1. Redactar general_objective sintetizando los objetivos de mayor nivel Bloom
2. Listar specific_objectives como bullets de cada LearningObjective
3. Generar weekly_map en Markdown (tabla 4 semanas con tema, Bloom, actividades)
4. Diseñar case_studies_design vinculados a la realidad profesional del egresado
5. Definir evaluation_criteria alineados a las competencias mapeadas
6. Retornar DescriptiveCard versión "V1"
