"""
Agente DI — AgentCore Runtime + Strands SDK.
Fase 3: Estructuración — Carta Descriptiva V1 con alineación Bloom–Competencias.

Patrón: BedrockAgentCoreApp + @app.entrypoint + lazy Strands Agent
"""
from __future__ import annotations

import json
import os
import re

import boto3
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext

app = BedrockAgentCoreApp()

_di_agent = None


def _get_agent():
    """Lazy init — only create Strands Agent on first invocation."""
    global _di_agent
    if _di_agent is not None:
        return _di_agent

    from strands import Agent, tool
    from strands.models import BedrockModel

    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-6",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        temperature=0.0,
        max_tokens=16384,
    )

    @tool
    def generate_learning_objectives(
        learning_outcomes: list,
        competencies: list,
        subject_type: str,
        knowledge_matrix: list,
    ) -> dict:
        """Generate learning objectives aligned to Bloom's Taxonomy and program competencies.

        Args:
            learning_outcomes: List of dicts with ra_id and description
            competencies: List of dicts with competency_id and description
            subject_type: One of FUNDAMENTOS, CONCENTRACION, PROYECTO
            knowledge_matrix: Knowledge matrix entries from Scholar agent
        """
        from src.agents.di.bloom_mapper import map_objective_to_competencies, select_bloom_verb

        objectives = []
        gaps = []
        for i, lo in enumerate(learning_outcomes):
            verb, level = select_bloom_verb(subject_type, i)
            obj_desc = f"{verb.capitalize()} {lo['description'].lower()}"
            obj_id = f"OBJ-{i+1:03d}"
            matched = map_objective_to_competencies(obj_desc, competencies)
            if not matched:
                matched = map_objective_to_competencies(lo["description"], competencies)
            if not matched:
                gaps.append({"objective_id": obj_id, "description": obj_desc, "ra_ids": [lo["ra_id"]], "reason": "No competency match"})
            objectives.append({
                "objective_id": obj_id, "description": obj_desc,
                "bloom_verb": verb, "bloom_level": level.value,
                "competency_ids": matched, "ra_ids": [lo["ra_id"]],
            })
        return {"objectives": objectives, "alignment_gaps": gaps}

    @tool
    def build_descriptive_card(
        objectives: list,
        subject_type: str,
        subject_name: str,
        graduation_profile: str,
        knowledge_matrix: list,
    ) -> dict:
        """Build the Descriptive Card V1 with 4-week map.

        Args:
            objectives: List of learning objective dicts
            subject_type: One of FUNDAMENTOS, CONCENTRACION, PROYECTO
            subject_name: Name of the subject
            graduation_profile: Graduate profile description
            knowledge_matrix: Knowledge matrix from Scholar agent
        """
        from src.agents.di.models import BloomLevel, LearningObjective
        from src.agents.di.card_builder import build_content_map, draft_descriptive_card

        lo_objects = [
            LearningObjective(
                objective_id=o["objective_id"], description=o["description"],
                bloom_verb=o["bloom_verb"], bloom_level=BloomLevel(o["bloom_level"]),
                competency_ids=o.get("competency_ids", []), ra_ids=o.get("ra_ids", []),
            ) for o in objectives
        ]
        content_map = build_content_map(subject_type, knowledge_matrix)
        card = draft_descriptive_card(content_map, lo_objects, subject_name, graduation_profile)
        return {
            "descriptive_card": card.to_dict(),
            "content_map": {"weeks": [
                {"week": w.week, "theme": w.theme, "bloom_level": w.bloom_level.value, "activities": w.activities}
                for w in content_map.weeks
            ]},
        }

    _di_agent = Agent(
        model=model,
        tools=[generate_learning_objectives, build_descriptive_card],
        system_prompt=(
            "You are DI, an instructional design agent. "
            "Call generate_learning_objectives then build_descriptive_card. "
            "Use EXACT competency IDs (C1,C2,C3,C4) and RA IDs (RA1,RA2) from input. "
            "Subject name and weeks must match the syllabus exactly. "
            "Return a single JSON block: ```json\n{...}\n``` "
            "Keys: objectives, traceability_matrix, descriptive_card, content_map, alignment_gaps. "
            "No extra text outside the JSON block."
        ),
    )
    return _di_agent


def _load_subject_context(subject_id: str) -> dict:
    """Load the subject JSON from S3 to get academic inputs and research results."""
    bucket = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
    s3 = boto3.client("s3")
    try:
        obj = s3.get_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json")
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return {}


def _build_di_prompt(subject_id: str, sj: dict) -> str:
    """Build a compact prompt with academic context for the DI agent."""
    meta = sj.get("metadata", {})
    inputs = sj.get("academic_inputs", {})
    research = sj.get("research", {})

    subject_name = meta.get("subject_name", "Unknown")
    subject_type = meta.get("subject_type", "CONCENTRACION")
    grad_profile = inputs.get("graduation_profile", "")[:200]
    competencies = inputs.get("competencies", [])
    learning_outcomes = inputs.get("learning_outcomes", [])
    syllabus = inputs.get("syllabus", "")
    papers = research.get("top20_papers", [])

    comp_text = "\n".join(f"  {c['competency_id']}: {c['description'][:80]}" for c in competencies)
    lo_text = "\n".join(f"  {lo['ra_id']}: {lo['description'][:80]}" for lo in learning_outcomes)
    papers_text = ", ".join(f"\"{p.get('title','')[:40]}\" ({p.get('year','')})" for p in papers[:10])

    return f"""Design instructional content for "{subject_name}" (ID: {subject_id}, type: {subject_type}).

Graduation profile: {grad_profile}

Competencies (use EXACT IDs):
{comp_text}

Learning Outcomes (use EXACT IDs):
{lo_text}

Syllabus:
{syllabus}

Top papers: {papers_text}

CALL generate_learning_objectives then build_descriptive_card.
Use EXACT IDs: {', '.join(c['competency_id'] for c in competencies)} and {', '.join(lo['ra_id'] for lo in learning_outcomes)}.
Weeks must match syllabus topics. Subject name must be "{subject_name}".
Return JSON with keys: objectives, traceability_matrix, descriptive_card, content_map, alignment_gaps.
"""


@app.entrypoint
def invoke(payload: dict, context: RequestContext = None) -> dict:
    """AgentCore Runtime entrypoint for DI Agent."""
    prompt = payload.get("prompt", "")
    subject_id = payload.get("subject_id", "")

    if not prompt and not subject_id:
        return {"result": "DI Agent ready. Send a prompt or subject_id to begin instructional design."}

    agent = _get_agent()

    if subject_id:
        sj = _load_subject_context(subject_id)
        if sj:
            prompt = _build_di_prompt(subject_id, sj)
        else:
            prompt = json.dumps({
                "task": "Design instructional content for this subject",
                "subject_id": subject_id,
                "instructions": "Use generate_learning_objectives and build_descriptive_card tools",
            })

    result = agent(prompt)
    result_str = str(result)

    if subject_id:
        try:
            _self_persist_di(subject_id, result_str)
        except Exception:
            pass

    return {"result": result_str}


def _self_persist_di(subject_id: str, result_text: str) -> None:

    from datetime import datetime, timezone

    bucket = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
    table_name = os.environ.get("SUBJECTS_TABLE_NAME", "academic-pipeline-subjects-dev")
    s3 = boto3.client("s3")
    ddb = boto3.resource("dynamodb")

    obj = s3.get_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json")
    sj = json.loads(obj["Body"].read().decode("utf-8"))

    parsed = {}
    matches = re.findall(r'```(?:json)?\s*\n(.*?)\n```', result_text, re.DOTALL)
    for m in matches:
        try:
            p = json.loads(m.strip())
            if isinstance(p, dict) and len(p) > len(parsed):
                parsed = p
        except json.JSONDecodeError:
            continue

    sj.setdefault("instructional_design", {})
    for key in ["objectives", "learning_objectives"]:
        if parsed.get(key):
            sj["instructional_design"]["learning_objectives"] = parsed[key]
            break
    if parsed.get("traceability_matrix"):
        sj["instructional_design"]["traceability_matrix"] = parsed["traceability_matrix"]
    if parsed.get("descriptive_card"):
        sj["instructional_design"]["descriptive_card"] = parsed["descriptive_card"]
    if parsed.get("content_map"):
        sj["instructional_design"]["content_map"] = parsed["content_map"]

    now = datetime.now(timezone.utc).isoformat()
    sj["pipeline_state"]["current_state"] = "DI_READY"
    sj["pipeline_state"]["state_history"].append({"state": "DI_READY", "agent": "di-agent", "timestamp": now, "llm_version": "claude-sonnet-4.6", "result_hash": ""})
    sj["updated_at"] = now

    s3.put_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json", Body=json.dumps(sj, ensure_ascii=False, indent=2).encode("utf-8"), ContentType="application/json")
    ddb.Table(table_name).put_item(Item={"subject_id": subject_id, "SK": "STATE", "current_state": "DI_READY", "subject_name": sj["metadata"]["subject_name"], "program_name": sj["metadata"]["program_name"], "updated_at": now, "s3_key": f"subjects/{subject_id}/subject.json"})


if __name__ == "__main__":
    app.run()
