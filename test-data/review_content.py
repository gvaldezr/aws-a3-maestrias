"""Review content of Ciencia de datos aplicada a las finanzas."""
import json

with open("test-data/ciencia-datos-finanzas-output.json") as f:
    sj = json.load(f)

SEP = "=" * 80

print(SEP)
print("ASIGNATURA: Ciencia de datos aplicada a las finanzas")
print("PROGRAMA: Maestria en Direccion y Tecnologia Financiera")
print("TIPO: CONCENTRACION | IDIOMA: ES")
print(SEP)

# 1. RESEARCH
print(f"\n{SEP}")
print("1. INVESTIGACION ACADEMICA")
print(SEP)
papers = sj.get("research", {}).get("top20_papers", [])
print(f"\nKeywords: {sj.get('research',{}).get('keywords',[])}")
print(f"\nPapers ({len(papers)}):")
for i, p in enumerate(papers, 1):
    print(f"  {i:2}. {p.get('title','')}")
    print(f"      {p.get('journal','')[:45]} | {p.get('year','')} | {p.get('key_finding','')}")

# 2. INSTRUCTIONAL DESIGN
print(f"\n{SEP}")
print("2. DISENO INSTRUCCIONAL")
print(SEP)
objectives = sj.get("instructional_design", {}).get("learning_objectives", [])
print(f"\nObjetivos ({len(objectives)}):")
for o in objectives:
    print(f"  {o.get('objective_id','')}: [{o.get('bloom_level','')}] {o.get('description','')}")
    print(f"    Competencias: {o.get('competency_ids',[])} | RAs: {o.get('ra_ids',[])}")

card = sj.get("instructional_design", {}).get("descriptive_card", {})
if card:
    print(f"\nCarta Descriptiva V1:")
    print(f"  Objetivo General: {card.get('general_objective','')[:150]}")
    print(f"  Especificos: {len(card.get('specific_objectives',[]))}")
    for so in card.get("specific_objectives", []):
        if isinstance(so, dict):
            print(f"    - {so.get('text', so.get('description', str(so)))[:100]}")
        else:
            print(f"    - {str(so)[:100]}")
    print(f"  Mapa Semanal:\n{card.get('weekly_map','')[:400]}")

cmap = sj.get("instructional_design", {}).get("content_map", {})
if cmap and cmap.get("weeks"):
    print(f"\nMapa de Contenidos:")
    for w in cmap["weeks"]:
        print(f"  Sem {w.get('week','')}: {w.get('theme','')} [{w.get('bloom_level','')}]")

# 3. CONTENT
print(f"\n{SEP}")
print("3. PAQUETE DE CONTENIDO")
print(SEP)
pkg = sj.get("content_package", {})

readings_data = pkg.get("executive_readings", {})
if isinstance(readings_data, dict):
    readings = readings_data.get("readings", [])
    print(f"\n  Asignatura (lecturas): {readings_data.get('subject_name','')}")
    print(f"  Idioma: {readings_data.get('language','')} | Semanas: {readings_data.get('total_weeks','')}")
else:
    readings = readings_data if isinstance(readings_data, list) else []
print(f"\nLecturas ({len(readings)}):")
for r in readings:
    if isinstance(r, str):
        print(f"  [STRING] {r[:100]}")
        continue
    print(f"  Sem {r.get('week','')}: {r.get('title','')}")
    md = r.get("content_md", "")
    for line in md.split("\n")[:6]:
        if line.strip():
            print(f"    {line.strip()[:80]}")

quizzes_data = pkg.get("quizzes", {})
if isinstance(quizzes_data, dict):
    quizzes = quizzes_data.get("quizzes", [])
    print(f"\n  Asignatura (quizzes): {quizzes_data.get('subject_name','')}")
    print(f"  Idioma: {quizzes_data.get('language','')} | RAs: {quizzes_data.get('total_learning_outcomes','')}")
else:
    quizzes = quizzes_data if isinstance(quizzes_data, list) else []
print(f"\nQuizzes ({len(quizzes)}):")
for q in quizzes:
    print(f"  {q.get('ra_id','')}: {len(q.get('questions',[]))} preguntas")
    for qq in q.get("questions", []):
        print(f"    P: {qq.get('question','')[:80]}")
        for oi, opt in enumerate(qq.get("options", [])):
            mark = " [OK]" if oi == qq.get("correct_answer", -1) else ""
            print(f"      {chr(65+oi)}) {opt[:60]}{mark}")
        print(f"    Feedback: {qq.get('feedback','')[:80]}")

# 4. MAESTRIA ARTIFACTS
print(f"\n{SEP}")
print("4. ARTEFACTOS MAESTRIA")
print(SEP)
ma = pkg.get("maestria_artifacts", {})
if ma:
    print(f"\n  Asignatura (artefactos): {ma.get('subject_name','')}")
    print(f"  Idioma: {ma.get('language','')}")
    ed = ma.get("evidence_dashboard", {})
    print(f"\n4.1 Dashboard de Evidencia ({len(ed.get('html_content',''))} chars):")
    print(f"  {ed.get('html_content','')[:400]}")

    cp = ma.get("critical_path_map", {})
    print(f"\n4.2 Mapa Ruta Critica ({len(cp.get('markdown_content',''))} chars):")
    print(f"  {cp.get('markdown_content','')[:400]}")

    cr = ma.get("executive_cases_repository", {})
    cases = cr.get("cases", [])
    print(f"\n4.3 Casos Ejecutivos ({len(cases)}):")
    for c in cases:
        print(f"  Titulo: {c.get('title','')}")
        print(f"  Contexto: {c.get('context','')[:150]}")
        print(f"  Preguntas: {c.get('questions',[])}")
        print(f"  Rubrica: {c.get('rubric',{}).get('criteria',[])} -> {c.get('rubric',{}).get('competency_ids',[])}")

    fg = ma.get("facilitator_guide", {})
    sessions = fg.get("sessions", [])
    print(f"\n4.4 Guia Facilitador ({len(sessions)} sesiones):")
    for s in sessions:
        print(f"  Sem {s.get('week','')}: {s.get('objective','')[:70]} ({s.get('duration_minutes','')} min)")
        for step in s.get("sequence", []):
            print(f"    {step.get('time',''):12} {step.get('activity','')[:50]}")
        for tq in s.get("trigger_questions", []):
            print(f"    Pregunta: {tq[:70]}")

print(f"\n{SEP}")
print(f"ESTADO: {sj['pipeline_state']['current_state']}")
print(SEP)
