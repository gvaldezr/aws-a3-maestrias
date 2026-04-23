"""Tests unitarios para card_builder — U3."""
from __future__ import annotations

import pytest

from src.agents.di.card_builder import build_content_map, build_weekly_map_markdown, draft_descriptive_card
from src.agents.di.models import BloomLevel, LearningObjective


def _obj(obj_id: str, level: BloomLevel = BloomLevel.ANALIZAR) -> LearningObjective:
    return LearningObjective(
        objective_id=obj_id, description=f"Objetivo {obj_id}",
        bloom_verb="analizar", bloom_level=level,
        competency_ids=["C1"], ra_ids=["RA1"],
    )


class TestBuildContentMap:
    def test_returns_exactly_4_weeks(self):
        content_map = build_content_map("CONCENTRACION", [])
        assert len(content_map.weeks) == 4

    def test_weeks_numbered_1_to_4(self):
        content_map = build_content_map("FUNDAMENTOS", [])
        assert [w.week for w in content_map.weeks] == [1, 2, 3, 4]

    def test_week_1_is_ingesta(self):
        content_map = build_content_map("CONCENTRACION", [])
        assert "Ingesta" in content_map.weeks[0].theme

    def test_week_4_is_sintesis(self):
        content_map = build_content_map("PROYECTO", [])
        assert "Síntesis" in content_map.weeks[3].theme

    def test_all_subject_types_produce_4_weeks(self):
        for stype in ["FUNDAMENTOS", "CONCENTRACION", "PROYECTO"]:
            cm = build_content_map(stype, [])
            assert len(cm.weeks) == 4


class TestBuildWeeklyMapMarkdown:
    def test_returns_markdown_table(self):
        cm = build_content_map("CONCENTRACION", [])
        md = build_weekly_map_markdown(cm)
        assert "| Semana |" in md
        assert "| 1 |" in md
        assert "| 4 |" in md

    def test_contains_all_4_weeks(self):
        cm = build_content_map("CONCENTRACION", [])
        md = build_weekly_map_markdown(cm)
        for i in range(1, 5):
            assert f"| {i} |" in md


class TestDraftDescriptiveCard:
    def test_version_is_v1(self):
        cm = build_content_map("CONCENTRACION", [])
        card = draft_descriptive_card(cm, [_obj("O1")], "Test Subject", "Egresado líder")
        assert card.version == "V1"

    def test_has_general_objective(self):
        cm = build_content_map("CONCENTRACION", [])
        card = draft_descriptive_card(cm, [_obj("O1")], "Test Subject", "Egresado líder")
        assert len(card.general_objective) > 0

    def test_weekly_map_is_markdown(self):
        cm = build_content_map("CONCENTRACION", [])
        card = draft_descriptive_card(cm, [_obj("O1")], "Test Subject", "Egresado líder")
        assert "| Semana |" in card.weekly_map

    def test_specific_objectives_max_6(self):
        cm = build_content_map("CONCENTRACION", [])
        objs = [_obj(f"O{i}") for i in range(10)]
        card = draft_descriptive_card(cm, objs, "Test Subject", "Egresado líder")
        assert len(card.specific_objectives) <= 6
