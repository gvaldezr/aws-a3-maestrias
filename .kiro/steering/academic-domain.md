---
inclusion: fileMatch
fileMatchPattern: "**/content*,**/di/*,**/scholar*,**/qa*,**/bloom*,**/carta*,**/reading*,**/quiz*,**/forum*,**/maestria*,**/canvas*"
---

# Dominio Académico — Conceptos Clave

## Contexto institucional
- **Universidad Anáhuac** — Programa MADTFIN (Maestría en Dirección y Tecnología Financiera)
- **Audiencia**: Directivos financieros con 5+ años de experiencia
- **Contexto regulatorio**: México (CNBV, Banxico, NIF)
- **LMS destino**: Canvas LMS (Instructure)

## Taxonomía de Bloom
Los objetivos de aprendizaje se clasifican en 6 niveles cognitivos (de menor a mayor):
1. **Recordar** — Identificar, reconocer
2. **Comprender** — Explicar, interpretar
3. **Aplicar** — Implementar, ejecutar
4. **Analizar** — Descomponer, examinar críticamente
5. **Evaluar** — Juzgar, fundamentar, defender
6. **Crear** — Diseñar, proponer soluciones originales

Para MADTFIN, los objetivos deben estar en nivel **Aplicar o superior**.

## Estructura de contenido por semana

Cada semana (= 1 Módulo en Canvas) contiene:
- 1 **Introducción** (150-200 palabras)
- 3 **Lecturas ejecutivas** (400-500 palabras cada una, prosa narrativa)
- 1 **Quiz** de razonamiento crítico (8 preguntas, ≥3 en Analizar/Evaluar)
- 1 **Foro** de aprendizaje (caso de negocio + 3 preguntas + rúbrica evaluación pares)

## Recursos globales (una vez por asignatura)
- 1 **Guión de Masterclass** (18-22 min, con indicaciones [SLIDE]/[CASO VISUAL])
- 1 **Reto de Aprendizaje Agéntico** (escenario financiero mexicano, rúbrica 4 niveles)

## 4 Artefactos obligatorios de Maestría (RF-05a)
1. **Dashboard de Evidencia** — Tabla con Top 20 papers indexados
2. **Mapa de Ruta Crítica** — Semana × Actividad × Entregable × Criterio
3. **Repositorio de Casos Ejecutivos** — Casos con rúbricas vinculadas a competencias
4. **Guía del Facilitador** — Sesiones de 90 min con secuencia, preguntas detonantes, criterios formativos

## Terminología clave

| Término | Significado |
|---------|------------|
| RA | Resultado de Aprendizaje (Learning Outcome) |
| Competencia | Competencia del programa (C1, C2, C3, C4) |
| Carta Descriptiva | Documento de diseño instruccional con objetivos, mapa de contenidos, trazabilidad |
| Knowledge Matrix | Matriz de conceptos, metodologías y casos extraídos de papers académicos |
| Subject JSON | JSON de fuente única de verdad por asignatura |
| QA Gate | Validación automática de cobertura de RAs y alineación Bloom |
| Checkpoint | Punto de validación humana donde el Staff aprueba/rechaza |

## Estructura en Canvas LMS

```
Curso: [Nombre Asignatura] — MADTFIN
├── Módulo "Información General"
│   ├── Carta Descriptiva
│   ├── Guión de Masterclass
│   └── Guía del Facilitador
├── Módulo "Semana 1: [Tema]"
│   ├── Introducción
│   ├── Lectura 1, 2, 3
│   ├── Quiz
│   └── Foro (con rúbrica HTML)
├── ... (Semanas 2-N)
└── Módulo "Reto de Aprendizaje Agéntico"
    └── Reto + Rúbrica (4 niveles, tabla HTML con colores)
```

## Rúbricas
- Renderizadas como **tablas HTML con colores** (4 niveles)
- Vinculadas a competencias del programa por ID
- Niveles: Insuficiente / En desarrollo / Competente / Destacado
