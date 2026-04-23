# Modelo de Lógica de Negocio — U4: Agente Content

## generate_content_package(subject_json) → ContentPackage
1. Leer: descriptive_card, learning_objectives, top20_papers, language, program_type
2. Generar executive_readings (1 por semana del mapa de 4 semanas)
3. Generar masterclass_scripts (1 por semana)
4. Generar quizzes (mínimo 3 preguntas por RA — BR-C03)
5. Generar lab_cases vinculados a competencias (BR-C07)
6. Si program_type == "MAESTRIA": generar maestria_artifacts (BR-C02)
7. Generar apa_bibliography desde top20_papers
8. Retornar ContentPackage completo

## generate_evidence_dashboard(papers) → EvidenceDashboard
1. Para cada paper del Top 20: extraer título, autores, año, revista, cuartil, hallazgo
2. Generar tabla Markdown/HTML con los campos anteriores (BR-C08)
3. Retornar EvidenceDashboard con html_content

## generate_critical_path_map(descriptive_card) → CriticalPathMap
1. Extraer el mapa de 4 semanas de la Carta Descriptiva
2. Generar tabla de 3 semanas de trabajo independiente (semanas 2, 3, 4)
3. Incluir: actividades, hitos de entrega, criterios de avance
4. Retornar CriticalPathMap con markdown_content

## generate_facilitator_guide(descriptive_card, objectives) → FacilitatorGuide
1. Para cada semana del mapa: generar sesión con minuto a minuto
2. Incluir: objetivo de sesión, secuencia de actividades, tiempos, preguntas detonadoras, criterios formativos
3. Retornar FacilitatorGuide con lista de sesiones

## validate_ra_coverage(content_package, learning_outcomes) → CoverageReport
1. Recopilar ra_ids cubiertos por quizzes y lab_cases
2. Comparar con lista completa de RA
3. Retornar CoverageReport con gaps y is_complete

## generate_apa_bibliography(papers) → list[str]
1. Para cada paper: formatear en APA 7: Autor(es). (Año). Título. Revista. DOI
2. Ordenar alfabéticamente por primer autor
3. Retornar lista de strings APA
