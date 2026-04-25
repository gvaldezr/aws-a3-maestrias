"""Check a subject's pipeline state."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ia_gen_subject.json"
with open(path) as f:
    sj = json.load(f)

print(f"Subject: {sj['metadata']['subject_name']}")
print(f"Program: {sj['metadata']['program_name']}")
print(f"Type: {sj['metadata'].get('subject_type', '')}")
print(f"State: {sj['pipeline_state']['current_state']}")
print(f"History: {len(sj['pipeline_state']['state_history'])} transitions")
for h in sj["pipeline_state"]["state_history"]:
    print(f"  {h['state']} ({h['agent']}) @ {h['timestamp'][:19]}")

papers = sj.get("research", {}).get("top20_papers", [])
keywords = sj.get("research", {}).get("keywords", [])
objs = sj.get("instructional_design", {}).get("learning_objectives", [])
card = sj.get("instructional_design", {}).get("descriptive_card", {})

cp = sj.get("content_package", {})
er = cp.get("executive_readings", {})
readings = er.get("readings", []) if isinstance(er, dict) else (er if isinstance(er, list) else [])
qz = cp.get("quizzes", {})
quizzes = qz.get("quizzes", []) if isinstance(qz, dict) else (qz if isinstance(qz, list) else [])
ma = cp.get("maestria_artifacts", {})

print(f"\nPapers: {len(papers)}")
print(f"Keywords: {keywords[:5]}")
print(f"Objectives: {len(objs)}")
print(f"Card: {card.get('subject_name', '')}")
print(f"Readings: {len(readings)}")
print(f"Quizzes: {len(quizzes)}")
print(f"Maestria: {bool(ma.get('evidence_dashboard'))}")
print(f"Syllabus: {sj.get('academic_inputs', {}).get('syllabus', '')[:200]}")

# Show objectives
for o in objs:
    print(f"  {o.get('objective_id','')}: [{o.get('bloom_level','')}] {o.get('description','')[:70]}")
