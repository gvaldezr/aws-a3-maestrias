"""
Agente DI — AgentCore Runtime + Strands SDK.
Fase 3: Estructuración — Carta Descriptiva V1 con alineación Bloom–Competencias.

Patrón: BedrockAgentCoreApp + @app.entrypoint + lazy Strands Agent
"""
from __future__ import annotations

import json
import os

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
        max_tokens=8192,
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
            "You are DI, an instructional design agent for professional Master's programs. "
            "Use generate_learning_objectives first, then build_descriptive_card. "
            "Return JSON with: objectives, traceability_matrix, descriptive_card, content_map, alignment_gaps"
        ),
    )
    return _di_agent


@app.entrypoint
def invoke(payload: dict, context: RequestContext = None) -> dict:
    """AgentCore Runtime entrypoint for DI Agent."""
    prompt = payload.get("prompt", "")
    subject_id = payload.get("subject_id", "")

    if not prompt and not subject_id:
        return {"result": "DI Agent ready. Send a prompt or subject_id to begin instructional design."}

    agent = _get_agent()

    if subject_id:
        prompt = json.dumps({
            "task": "Design instructional content for this subject",
            "subject_id": subject_id,
            "instructions": "Use generate_learning_objectives and build_descriptive_card tools",
        })

    result = agent(prompt)
    return {"result": str(result)}


if __name__ == "__main__":
    app.run()
