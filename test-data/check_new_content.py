"""Check if masterclass and agentic challenge were generated."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/estadistica_final.json"
with open(path) as f:
    sj = json.load(f)

cp = sj.get("content_package", {})
print(f"Subject: {sj['metadata']['subject_name']}")
print(f"State: {sj['pipeline_state']['current_state']}")

er = cp.get("executive_readings", {})
readings = er.get("readings", []) if isinstance(er, dict) else (er if isinstance(er, list) else [])
qz = cp.get("quizzes", {})
quizzes = qz.get("quizzes", []) if isinstance(qz, dict) else (qz if isinstance(qz, list) else [])

print(f"Readings: {len(readings)}")
print(f"Quizzes: {len(quizzes)}")
print(f"Maestria: {bool(cp.get('maestria_artifacts', {}).get('evidence_dashboard'))}")

mc = cp.get("masterclass_script", {})
print(f"Masterclass: {bool(mc)}")
if mc:
    print(f"  Title: {mc.get('title', '')}")
    print(f"  Duration: {mc.get('duration_minutes', '')} min")
    print(f"  Sections: {len(mc.get('structure', []))}")
    for s in mc.get("structure", []):
        print(f"    {s.get('time', '')}: {s.get('section', '')}")

ac = cp.get("agentic_challenge", {})
print(f"Agentic Challenge: {bool(ac)}")
if ac:
    print(f"  Title: {ac.get('title', '')}")
    print(f"  Week: {ac.get('week', '')}")
    print(f"  Scenario: {ac.get('scenario', '')[:150]}...")
    print(f"  Central question: {ac.get('central_question', '')[:100]}...")
    rubric = ac.get("rubric", {})
    criteria = rubric.get("criteria", [])
    print(f"  Rubric: {len(criteria)} criteria")
    for c in criteria:
        print(f"    {c.get('criterion', '')}: {c.get('weight', '')}")
