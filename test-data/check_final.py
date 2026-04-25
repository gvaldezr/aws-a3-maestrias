"""Check final pipeline state."""
import json

with open("/tmp/final_v3.json") as f:
    sj = json.load(f)

state = sj["pipeline_state"]["current_state"]
papers = len(sj.get("research", {}).get("top20_papers", []))
objs = len(sj.get("instructional_design", {}).get("learning_objectives", []))
cp = sj.get("content_package", {})

er = cp.get("executive_readings", {})
if isinstance(er, dict):
    readings = len(er.get("readings", []))
elif isinstance(er, list):
    readings = len(er)
else:
    readings = 0

qz = cp.get("quizzes", {})
if isinstance(qz, dict):
    quizzes = len(qz.get("quizzes", []))
elif isinstance(qz, list):
    quizzes = len(qz)
else:
    quizzes = 0

ma = cp.get("maestria_artifacts", {})
has_dashboard = bool(ma.get("evidence_dashboard", {}).get("html_content", "")) if isinstance(ma, dict) else False
has_cases = bool(ma.get("executive_cases_repository", {}).get("cases", [])) if isinstance(ma, dict) else False
has_guide = bool(ma.get("facilitator_guide", {}).get("sessions", [])) if isinstance(ma, dict) else False

print(f"State: {state}")
print(f"Papers: {papers} | Objectives: {objs}")
print(f"Readings: {readings} | Quizzes: {quizzes}")
print(f"Dashboard: {has_dashboard} | Cases: {has_cases} | Guide: {has_guide}")
print()

all_ok = (
    state == "CONTENT_READY"
    and papers > 0
    and objs > 0
    and readings > 0
    and quizzes > 0
    and has_dashboard
)

if all_ok:
    print("✅ PIPELINE COMPLETO — AUTO-PERSISTENCIA FUNCIONA EN LAS 3 FASES")
else:
    print(f"⚠️ Parcial")
