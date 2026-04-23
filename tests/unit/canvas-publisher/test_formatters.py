"""Tests unitarios y PBT para formatters — U6."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.canvas_publisher.formatters import (
    format_apa_page_payload,
    format_page_payload,
    format_quiz_payload,
    format_quiz_question_payload,
    format_rubric_payload,
    markdown_to_html,
)


class TestMarkdownToHtml:
    def test_empty_returns_empty(self):
        assert markdown_to_html("") == ""

    def test_h1_converted(self):
        assert "<h1>Title</h1>" in markdown_to_html("# Title")

    def test_h2_converted(self):
        assert "<h2>Section</h2>" in markdown_to_html("## Section")

    def test_bold_converted(self):
        assert "<strong>bold</strong>" in markdown_to_html("**bold**")

    def test_italic_converted(self):
        assert "<em>italic</em>" in markdown_to_html("*italic*")

    def test_list_item_converted(self):
        result = markdown_to_html("- item one")
        assert "<li>item one</li>" in result

    def test_plain_text_wrapped_in_p(self):
        result = markdown_to_html("Hello world")
        assert "<p>Hello world</p>" in result


class TestFormatPagePayload:
    def test_has_wiki_page_key(self):
        payload = format_page_payload("Title", "Content")
        assert "wiki_page" in payload

    def test_title_preserved(self):
        payload = format_page_payload("My Title", "Content")
        assert payload["wiki_page"]["title"] == "My Title"

    def test_published_false(self):
        payload = format_page_payload("T", "C")
        assert payload["wiki_page"]["published"] is False


class TestFormatQuizPayload:
    def test_has_quiz_key(self):
        payload = format_quiz_payload("Quiz RA1", "RA1")
        assert "quiz" in payload

    def test_title_preserved(self):
        payload = format_quiz_payload("Quiz RA1", "RA1")
        assert payload["quiz"]["title"] == "Quiz RA1"

    def test_published_false(self):
        payload = format_quiz_payload("Q", "RA1")
        assert payload["quiz"]["published"] is False


class TestFormatQuizQuestionPayload:
    def test_has_question_key(self):
        q = {"question": "What?", "options": ["A", "B", "C", "D"], "correct_answer": 0, "feedback": "OK"}
        payload = format_quiz_question_payload(q)
        assert "question" in payload

    def test_correct_answer_has_weight_100(self):
        q = {"question": "Q?", "options": ["A", "B"], "correct_answer": 1, "feedback": ""}
        payload = format_quiz_question_payload(q)
        answers = payload["question"]["answers"]
        assert answers[1]["answer_weight"] == 100
        assert answers[0]["answer_weight"] == 0

    def test_multiple_choice_type(self):
        q = {"question": "Q?", "options": ["A", "B"], "correct_answer": 0, "feedback": ""}
        payload = format_quiz_question_payload(q)
        assert payload["question"]["question_type"] == "multiple_choice_question"


class TestFormatRubricPayload:
    def test_has_rubric_key(self):
        payload = format_rubric_payload("Rubric", ["Criterion 1"], ["C1"])
        assert "rubric" in payload

    def test_competency_ids_in_title(self):
        payload = format_rubric_payload("Rubric", ["C1"], ["COMP-01"])
        assert "COMP-01" in payload["rubric"]["title"]

    def test_criteria_count_matches(self):
        payload = format_rubric_payload("R", ["C1", "C2", "C3"], ["C1"])
        assert len(payload["rubric"]["criteria"]) == 3


class TestFormatApaBibliography:
    def test_has_wiki_page_key(self):
        payload = format_apa_page_payload(["García, J. (2023). Title. Journal."])
        assert "wiki_page" in payload

    def test_title_is_referencias(self):
        payload = format_apa_page_payload([])
        assert "Referencias" in payload["wiki_page"]["title"]

    def test_references_in_body(self):
        payload = format_apa_page_payload(["Smith, J. (2022). Paper. Journal."])
        assert "Smith, J." in payload["wiki_page"]["body"]


class TestFormattersPBT:
    @given(st.text(min_size=0, max_size=500))
    @settings(max_examples=30)
    def test_markdown_to_html_always_returns_string(self, md: str):
        """PBT-03 invariant: markdown_to_html siempre retorna string."""
        result = markdown_to_html(md)
        assert isinstance(result, str)

    @given(st.text(min_size=1, max_size=100), st.text(min_size=0, max_size=200))
    @settings(max_examples=30)
    def test_format_page_payload_always_has_wiki_page(self, title: str, content: str):
        """PBT-03 invariant: format_page_payload siempre tiene wiki_page."""
        payload = format_page_payload(title, content)
        assert "wiki_page" in payload
        assert payload["wiki_page"]["title"] == title

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=20))
    @settings(max_examples=20)
    def test_apa_page_count_preserved(self, refs: list[str]):
        """PBT-02 round-trip: número de referencias preservado en el body."""
        payload = format_apa_page_payload(refs)
        body = payload["wiki_page"]["body"]
        assert body.count("<p>") == len(refs)
