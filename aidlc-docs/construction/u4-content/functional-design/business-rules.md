# Reglas de Negocio — U4: Agente Content

## BR-C01 — Paquete completo obligatorio
El agente debe generar todos los componentes del ContentPackage: lecturas ejecutivas, guiones de masterclass, quizzes y casos de laboratorio. No se acepta un paquete parcial.

## BR-C02 — Cuatro artefactos de Maestría obligatorios
Para programas de Maestría (program_type == "MAESTRIA"), los cuatro artefactos de RF-05a son obligatorios: Dashboard de Evidencia, Mapa de Ruta Crítica, Repositorio de Casos Ejecutivos y Guía del Facilitador.

## BR-C03 — Mínimo 3 preguntas por RA en quizzes
Cada RA de la asignatura debe tener al menos 3 preguntas de quiz con respuesta correcta y retroalimentación.

## BR-C04 — Idioma según configuración
El contenido se genera en el idioma configurado en el JSON de la asignatura (ES / EN / BILINGUAL). En modo BILINGUAL, cada recurso tiene secciones paralelas en ambos idiomas.

## BR-C05 — Cobertura 100% de RA
El paquete de contenido debe cubrir el 100% de los RA. Si algún RA no tiene contenido asociado, el agente reintenta (máx. 3 veces) antes de escalar.

## BR-C06 — Reintentos con prompt diferente
Cada reintento usa un prompt distinto para evitar el mismo resultado fallido. El log de cada intento se almacena en el JSON.

## BR-C07 — Rúbricas vinculadas a competencias
Las rúbricas de los casos de laboratorio deben referenciar competency_ids del programa.

## BR-C08 — Dashboard de Evidencia desde corpus Scopus
El Dashboard de Evidencia se genera exclusivamente a partir del Top 20 de papers del Agente Scholar (no se inventan papers).
