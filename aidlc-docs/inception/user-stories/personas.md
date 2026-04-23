# Personas del Sistema
## Pipeline Académico → Canvas LMS

---

## Persona 1 — Staff de Tecnología Educativa

**Nombre representativo**: Sofía Ramírez
**Rol**: Especialista en Tecnología Educativa
**Organización**: Dirección de Innovación Académica

### Descripción
Sofía es responsable de transformar los insumos de planeación académica (Perfil de Egreso, Matrices de Competencias, temarios) en aulas virtuales operativas en Canvas LMS. Tiene conocimiento pedagógico sólido pero no es desarrolladora — interactúa con el sistema a través de una interfaz web sin necesidad de acceder a la consola de AWS.

### Motivaciones
- Reducir el tiempo de montaje de un curso de semanas a horas
- Garantizar que el contenido generado esté alineado al Perfil de Egreso institucional
- Tener visibilidad del estado de cada asignatura en proceso
- Aprobar o rechazar el contenido antes de que llegue a los docentes

### Frustraciones
- Procesos manuales repetitivos de carga y formateo de contenido
- Falta de trazabilidad entre los objetivos de aprendizaje y las competencias del programa
- Errores de publicación en Canvas que requieren intervención técnica

### Nivel técnico
Medio — maneja herramientas de productividad, Canvas LMS y plataformas de gestión académica. No requiere conocimientos de AWS o programación.

### Historias asociadas
US-01, US-02, US-03, US-04, US-05, US-06, US-07, US-08, US-14, US-15, US-16

---

## Persona 2 — Agente Scholar (Sistema)

**Nombre representativo**: Scholar Agent
**Rol**: Agente de Investigación Académica
**Tecnología**: Amazon Bedrock Agent + Scopus API Action Group

### Descripción
Agente de IA especializado en investigación académica. Opera autónomamente para transformar los Resultados de Aprendizaje y competencias de una asignatura en un corpus de evidencia científica validada (Top 20 papers Q1/Q2) y una Matriz de Conocimiento Académico.

### Responsabilidades
- Generar keywords de búsqueda de alta precisión a partir de RA y competencias
- Ejecutar búsquedas en Scopus con filtros de impacto (Q1/Q2)
- Extraer conceptos, metodologías y casos de éxito con enfoque directivo
- Escalar cuando la búsqueda no produce resultados suficientes o de calidad

### Historias asociadas
US-09, US-10, US-17

---

## Persona 3 — Agente DI (Sistema)

**Nombre representativo**: DI Agent
**Rol**: Agente de Diseño Instruccional
**Tecnología**: Amazon Bedrock Agent (Claude Sonnet)

### Descripción
Agente de IA especializado en diseño instruccional. Transforma el corpus académico y el Perfil de Egreso en una Carta Descriptiva V1 con objetivos de aprendizaje alineados a la Taxonomía de Bloom y mapeados a competencias del programa.

### Responsabilidades
- Organizar el conocimiento según el tipo de materia (Fundamentos, Concentración, Proyecto)
- Redactar objetivos de aprendizaje con verbos Bloom en nivel Analizar/Evaluar
- Mapear cada objetivo a competencias del programa por ID
- Escalar cuando detecta gaps de alineación Bloom–Competencias

### Historias asociadas
US-11, US-18

---

## Persona 4 — Agente Content (Sistema)

**Nombre representativo**: Content Agent
**Rol**: Agente de Generación de Contenido
**Tecnología**: Amazon Bedrock Agent (Claude Sonnet / Haiku)

### Descripción
Agente de IA especializado en producción de contenido educativo ejecutivo. Genera el paquete multimedia completo a partir de la Carta Descriptiva V1, incluyendo los cuatro artefactos obligatorios para programas de Maestría.

### Responsabilidades
- Generar lecturas ejecutivas, guiones de masterclass, quizzes y casos de laboratorio agéntico
- Producir los cuatro artefactos de Maestría: Dashboard de Evidencia, Mapa de Ruta Crítica, Repositorio de Casos Ejecutivos y Guía del Facilitador
- Generar contenido bilingüe (Español/Inglés) según configuración
- Escalar cuando el contenido generado no cubre el 100% de los RA

### Historias asociadas
US-12, US-13, US-19

---

## Persona 5 — Administrador del Sistema (Seguridad)

**Nombre representativo**: Carlos Mendoza
**Rol**: Administrador de Infraestructura Educativa
**Organización**: Dirección de TI / DevOps

### Descripción
Carlos gestiona las credenciales, configuraciones de seguridad y accesos del sistema. Es responsable de rotar las API Keys de Scopus y Canvas, gestionar los usuarios del Staff de Tecnología Educativa y monitorear el estado operativo del pipeline.

### Motivaciones
- Garantizar que las credenciales nunca estén expuestas en código o logs
- Controlar quién puede disparar el pipeline y aprobar publicaciones
- Tener visibilidad de fallos y alertas de seguridad en tiempo real

### Nivel técnico
Alto — acceso a AWS Console, Secrets Manager y CloudWatch.

### Historias asociadas
US-14, US-15, US-16

---
