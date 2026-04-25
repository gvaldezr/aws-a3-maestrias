"""Check if the Step Functions pipeline persisted results for Fundamentos."""
import json
import boto3

subject_id = "bee8b380-77c2-4ee0-9b1c-93113506b9d2"
bucket = "academic-pipeline-subjects-254508868459-us-east-1-dev"

s3 = boto3.client("s3")
obj = s3.get_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json")
sj = json.loads(obj["Body"].read().decode("utf-8"))

state = sj["pipeline_state"]["current_state"]
history = sj["pipeline_state"]["state_history"]

print(f"Subject: {sj['metadata']['subject_name']}")
print(f"State: {state}")
print(f"History: {len(history)} transitions")
for h in history:
    print(f"  {h['state']} ({h['agent']}) @ {h['timestamp'][:19]}")

papers = sj.get("research", {}).get("top20_papers", [])
keywords = sj.get("research", {}).get("keywords", [])
km = sj.get("research", {}).get("knowledge_matrix", [])
print(f"\nScholar: {len(papers)} papers, {len(keywords)} keywords, {len(km)} KM entries")
if papers:
    for p in papers[:3]:
        print(f"  - {p.get('title','')[:60]} ({p.get('year','')})")

objs = sj.get("instructional_design", {}).get("learning_objectives", [])
card = sj.get("instructional_design", {}).get("descriptive_card", {})
cmap = sj.get("instructional_design", {}).get("content_map", {})
weeks = cmap.get("weeks", []) if isinstance(cmap, dict) else []
print(f"\nDI: {len(objs)} objectives, card='{card.get('subject_name','')}', {len(weeks)} weeks")
for o in objs:
    print(f"  {o.get('objective_id','')}: [{o.get('bloom_level','')}] {o.get('description','')[:60]}")
    print(f"    Comp: {o.get('competency_ids',[])} | RAs: {o.get('ra_ids',[])}")

cp = sj.get("content_package", {})
er = cp.get("executive_readings", {})
readings = er.get("readings", []) if isinstance(er, dict) else (er if isinstance(er, list) else [])
qz = cp.get("quizzes", {})
quizzes = qz.get("quizzes", []) if isinstance(qz, dict) else (qz if isinstance(qz, list) else [])
ma = cp.get("maestria_artifacts", {})
has_dash = bool(ma.get("evidence_dashboard", {}).get("html_content", "")) if isinstance(ma, dict) else False

print(f"\nContent: {len(readings)} readings, {len(quizzes)} quizzes, maestria={has_dash}")

print(f"\n{'='*60}")
if state == "CONTENT_READY" and papers and objs and readings and quizzes:
    print("PIPELINE COMPLETO VIA STEP FUNCTIONS + AUTO-PERSIST")
elif state == "CONTENT_READY" and not readings:
    print("CONTENT_READY pero sin readings (agentes auto-persistieron estado pero Content no guardo paquete)")
else:
    print(f"Estado parcial: {state}")

# Save locally for review
with open("/tmp/fundamentos_output.json", "w") as f:
    json.dump(sj, f, ensure_ascii=False, indent=2)
print(f"\nSaved to /tmp/fundamentos_output.json")
