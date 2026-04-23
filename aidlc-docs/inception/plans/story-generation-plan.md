# Plan de Generación de User Stories
## Pipeline Académico → Canvas LMS

Por favor responde cada pregunta llenando la letra de tu elección después de la etiqueta `[Answer]:`.

---

## Plan de Ejecución

- [x] Paso 1: Recopilar respuestas a preguntas de planificación
- [x] Paso 2: Definir personas
- [x] Paso 3: Determinar enfoque de desglose de historias
- [x] Paso 4: Generar `personas.md`
- [x] Paso 5: Generar `stories.md` con criterios de aceptación
- [x] Paso 6: Mapear personas a historias

---

## Preguntas de Planificación

### Pregunta 1 — Personas del Sistema
Además del **Staff de Tecnología Educativa**, ¿qué otros actores deben tener historias de usuario propias?

A) Solo el Docente/Facilitador (quien usa el aula generada en Canvas)
B) Docente/Facilitador + Administrador del sistema (quien gestiona configuraciones y credenciales)
C) Docente/Facilitador + Administrador + Estudiante (quien consume el curso en Canvas)
D) Solo el Staff de Tecnología Educativa (los demás actores son consumidores pasivos)
E) Otro (describe después de [Answer]:)

[Answer]: D

---

### Pregunta 2 — Enfoque de Desglose de Historias
¿Cómo prefieres organizar las historias de usuario?

A) Por flujo de usuario (carga → procesamiento → validación → publicación)
B) Por agente/componente del sistema (Scholar, DI, Content, Canvas)
C) Por persona (todas las historias del Staff juntas, luego las del Docente, etc.)
D) Por épica de negocio (Investigación, Diseño Instruccional, Producción, Publicación)
E) Otro (describe después de [Answer]:)

[Answer]: D

---

### Pregunta 3 — Granularidad de las Historias
¿Qué nivel de detalle deben tener las historias?

A) Épicas de alto nivel (5–10 historias que cubran el sistema completo)
B) Historias estándar (15–25 historias con criterios de aceptación detallados)
C) Historias granulares (30+ historias, una por cada flujo o caso de uso específico)
D) Otro (describe después de [Answer]:)

[Answer]: B

---

### Pregunta 4 — Historias del Sistema Agéntico
¿Deben incluirse historias de usuario para los agentes de IA (Scholar, DI, Content) como actores del sistema?

A) Sí — incluir historias técnicas del sistema con el agente como actor ("Como Agente Scholar, quiero...")
B) No — los agentes son implementación interna; solo historias de actores humanos
C) Parcial — solo para los flujos donde el agente escala o falla (casos de error)
D) Otro (describe después de [Answer]:)

[Answer]: A

---

### Pregunta 5 — Criterios de Aceptación
¿Qué formato prefieres para los criterios de aceptación?

A) Formato Gherkin (Given / When / Then)
B) Lista de verificación (checklist de condiciones)
C) Combinación: Gherkin para flujos principales, checklist para validaciones
D) Otro (describe después de [Answer]:)

[Answer]: C

---

### Pregunta 6 — Historias de Seguridad y Acceso
¿Deben incluirse historias explícitas para autenticación, autorización y gestión de credenciales (Scopus API Key, Canvas Token)?

A) Sí — incluir historias de seguridad como ciudadanos de primera clase
B) No — la seguridad se cubre como criterios de aceptación dentro de otras historias
C) Otro (describe después de [Answer]:)

[Answer]: A

---
