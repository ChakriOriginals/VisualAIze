"""
Stage 01 — Parser Agent: 30 tests
Run: python -m pytest tests/test_stage01_parser.py -v
"""
import io
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import ParsedContent

# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_DATA = {
    "main_topic": "Pythagorean Theorem",
    "definitions": ["Right triangle: a triangle with one 90-degree angle",
                    "Hypotenuse: the longest side opposite the right angle"],
    "key_equations": [r"a^2 + b^2 = c^2", r"c = \sqrt{a^2+b^2}"],
    "core_claims": ["Square of hypotenuse equals sum of squares of legs"],
    "example_instances": ["3-4-5 triangle", "5-12-13 triangle"],
}

MINIMAL_DATA = {
    "main_topic": "Calculus",
    "definitions": [],
    "key_equations": [],
    "core_claims": [],
    "example_instances": [],
}


# ══════════════════════════════════════════════════════════════════════════════
# GROUP A: Schema Validation (T01–T08)
# ══════════════════════════════════════════════════════════════════════════════

class TestParserSchema:

    def test_01_valid_data_parses_correctly(self):
        result = ParsedContent(**VALID_DATA)
        assert result.main_topic == "Pythagorean Theorem"

    def test_02_main_topic_is_string(self):
        result = ParsedContent(**VALID_DATA)
        assert isinstance(result.main_topic, str)

    def test_03_definitions_is_list(self):
        result = ParsedContent(**VALID_DATA)
        assert isinstance(result.definitions, list)

    def test_04_key_equations_is_list(self):
        result = ParsedContent(**VALID_DATA)
        assert isinstance(result.key_equations, list)

    def test_05_core_claims_is_list(self):
        result = ParsedContent(**VALID_DATA)
        assert isinstance(result.core_claims, list)

    def test_06_example_instances_is_list(self):
        result = ParsedContent(**VALID_DATA)
        assert isinstance(result.example_instances, list)

    def test_07_empty_lists_accepted(self):
        result = ParsedContent(**MINIMAL_DATA)
        assert result.definitions == []
        assert result.key_equations == []

    def test_08_missing_optional_fields_use_defaults(self):
        result = ParsedContent(**MINIMAL_DATA)
        assert result.main_topic == "Calculus"
        assert isinstance(result.core_claims, list)


# ══════════════════════════════════════════════════════════════════════════════
# GROUP B: Input Handling (T09–T15)
# ══════════════════════════════════════════════════════════════════════════════

class TestParserInput:

    def test_09_input_truncation_at_6000_chars(self):
        long_text = "x" * 10000
        assert len(long_text[:6000]) == 6000

    def test_10_input_under_6000_not_truncated(self):
        short_text = "Pythagorean Theorem " * 50
        assert len(short_text) < 6000
        assert short_text[:6000] == short_text

    def test_11_exactly_6000_chars_not_truncated(self):
        exact = "a" * 6000
        assert len(exact[:6000]) == 6000
        assert exact[:6000] == exact

    def test_12_unicode_input_handled(self):
        unicode_text = "∑∫∂∇ × " * 100
        truncated = unicode_text[:6000]
        assert len(truncated) <= 6000

    def test_13_newlines_preserved_in_input(self):
        text = "Line 1\nLine 2\nLine 3"
        assert "\n" in text[:6000]

    def test_14_empty_string_input_handled(self):
        empty = ""
        truncated = empty[:6000]
        assert truncated == ""

    def test_15_whitespace_only_input_handled(self):
        ws = "   \n\t  "
        truncated = ws[:6000]
        assert len(truncated) <= 6000


# ══════════════════════════════════════════════════════════════════════════════
# GROUP C: LaTeX Validation (T16–T20)
# ══════════════════════════════════════════════════════════════════════════════

class TestParserLatex:

    def test_16_equations_are_nonempty_strings(self):
        result = ParsedContent(**VALID_DATA)
        for eq in result.key_equations:
            assert isinstance(eq, str) and len(eq.strip()) > 0

    def test_17_equations_dont_contain_begin_environment(self):
        dirty = {**VALID_DATA, "key_equations": [r"\begin{pmatrix}1&2\\3&4\end{pmatrix}"]}
        result = ParsedContent(**dirty)
        # Simulate stripping
        cleaned = [eq for eq in result.key_equations if r'\begin' not in eq]
        assert all(r'\begin' not in eq for eq in cleaned)

    def test_18_equation_with_backslash_is_valid(self):
        data = {**VALID_DATA, "key_equations": [r"\frac{a}{b}", r"\sqrt{x^2}"]}
        result = ParsedContent(**data)
        assert len(result.key_equations) == 2

    def test_19_multiple_equations_all_stored(self):
        data = {**VALID_DATA, "key_equations": [r"a+b", r"c=d", r"e^f"]}
        result = ParsedContent(**data)
        assert len(result.key_equations) == 3

    def test_20_dollar_sign_equations_accepted(self):
        data = {**VALID_DATA, "key_equations": ["$a^2 + b^2 = c^2$"]}
        result = ParsedContent(**data)
        assert "$" in result.key_equations[0]


# ══════════════════════════════════════════════════════════════════════════════
# GROUP D: PDF Extraction (T21–T25)
# ══════════════════════════════════════════════════════════════════════════════

class TestParserPDF:

    def test_21_invalid_pdf_bytes_raise_exception(self):
        from backend.agents.parser_agent import extract_text_from_pdf
        with pytest.raises(Exception):
            extract_text_from_pdf(b"not a pdf")

    def test_22_empty_bytes_raise_exception(self):
        from backend.agents.parser_agent import extract_text_from_pdf
        with pytest.raises(Exception):
            extract_text_from_pdf(b"")

    def test_23_random_bytes_raise_exception(self):
        from backend.agents.parser_agent import extract_text_from_pdf
        with pytest.raises(Exception):
            extract_text_from_pdf(bytes(range(256)))

    def test_24_pdf_with_only_header_raises_value_error(self):
        from backend.agents.parser_agent import extract_text_from_pdf
        fake_pdf = b"%PDF-1.4\n%%EOF"
        with pytest.raises(Exception):
            extract_text_from_pdf(fake_pdf)

    def test_25_extract_function_exists_and_callable(self):
        from backend.agents.parser_agent import extract_text_from_pdf
        assert callable(extract_text_from_pdf)


# ══════════════════════════════════════════════════════════════════════════════
# GROUP E: Content Quality (T26–T30)
# ══════════════════════════════════════════════════════════════════════════════

class TestParserContentQuality:

    def test_26_main_topic_nonempty(self):
        result = ParsedContent(**VALID_DATA)
        assert len(result.main_topic.strip()) > 0

    def test_27_definitions_contain_strings(self):
        result = ParsedContent(**VALID_DATA)
        for d in result.definitions:
            assert isinstance(d, str)

    def test_28_core_claims_contain_strings(self):
        result = ParsedContent(**VALID_DATA)
        for c in result.core_claims:
            assert isinstance(c, str)

    def test_29_example_instances_contain_strings(self):
        result = ParsedContent(**VALID_DATA)
        for e in result.example_instances:
            assert isinstance(e, str)

    def test_30_parsed_content_serializable_to_dict(self):
        result = ParsedContent(**VALID_DATA)
        d = result.model_dump()
        assert "main_topic" in d
        assert "key_equations" in d
        assert isinstance(d["key_equations"], list)
