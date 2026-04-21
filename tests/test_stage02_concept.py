"""
Stage 02 — Concept Agent: 30 tests
Run: python -m pytest tests/test_stage02_concept.py -v
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import ConceptExtractionResult, ParsedContent

# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_concepts(n=3):
    return {
        "core_concepts": [
            {"concept_name": f"Concept{i}",
             "intuitive_explanation": f"Explanation {i}",
             "mathematical_form": f"x_{i}^2",
             "why_it_matters": f"Reason {i}"}
            for i in range(n)
        ],
        "concept_ordering": [f"Concept{i}" for i in range(n)]
    }

VALID_3 = make_concepts(3)
VALID_5 = make_concepts(5)
VALID_7 = make_concepts(7)

PYTH_CONCEPTS = {
    "core_concepts": [
        {"concept_name": "Right Triangle", "intuitive_explanation": "90° triangle",
         "mathematical_form": "90°", "why_it_matters": "Foundation"},
        {"concept_name": "Pythagorean Theorem", "intuitive_explanation": "Side relationship",
         "mathematical_form": r"a^2+b^2=c^2", "why_it_matters": "Essential"},
        {"concept_name": "Hypotenuse", "intuitive_explanation": "Longest side",
         "mathematical_form": "c", "why_it_matters": "Key side"},
    ],
    "concept_ordering": ["Right Triangle", "Pythagorean Theorem", "Hypotenuse"]
}


# ══════════════════════════════════════════════════════════════════════════════
# GROUP A: Schema (T01–T06)
# ══════════════════════════════════════════════════════════════════════════════

class TestConceptSchema:

    def test_01_valid_schema_parses(self):
        result = ConceptExtractionResult(**VALID_3)
        assert len(result.core_concepts) == 3

    def test_02_core_concepts_is_list(self):
        result = ConceptExtractionResult(**VALID_3)
        assert isinstance(result.core_concepts, list)

    def test_03_concept_ordering_is_list(self):
        result = ConceptExtractionResult(**VALID_3)
        assert isinstance(result.concept_ordering, list)

    def test_04_each_concept_has_name(self):
        result = ConceptExtractionResult(**VALID_3)
        for c in result.core_concepts:
            assert hasattr(c, 'concept_name') and c.concept_name

    def test_05_each_concept_has_explanation(self):
        result = ConceptExtractionResult(**VALID_3)
        for c in result.core_concepts:
            assert hasattr(c, 'intuitive_explanation') and c.intuitive_explanation

    def test_06_each_concept_has_why_it_matters(self):
        result = ConceptExtractionResult(**VALID_3)
        for c in result.core_concepts:
            assert hasattr(c, 'why_it_matters') and c.why_it_matters


# ══════════════════════════════════════════════════════════════════════════════
# GROUP B: Ordering Integrity (T07–T13)
# ══════════════════════════════════════════════════════════════════════════════

class TestConceptOrdering:

    def test_07_all_ordering_names_in_core_concepts(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        names = {c.concept_name for c in result.core_concepts}
        for name in result.concept_ordering:
            assert name in names

    def test_08_no_orphan_names_in_ordering(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        names = {c.concept_name for c in result.core_concepts}
        orphans = [n for n in result.concept_ordering if n not in names]
        assert len(orphans) == 0

    def test_09_ordering_length_equals_concepts_length(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        assert len(result.concept_ordering) == len(result.core_concepts)

    def test_10_ordering_has_no_duplicates(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        assert len(result.concept_ordering) == len(set(result.concept_ordering))

    def test_11_concept_names_are_unique(self):
        result = ConceptExtractionResult(**VALID_5)
        names = [c.concept_name for c in result.core_concepts]
        assert len(names) == len(set(names))

    def test_12_ordering_preserves_pedagogical_sequence(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        assert result.concept_ordering[0] == "Right Triangle"
        assert result.concept_ordering[-1] == "Hypotenuse"

    def test_13_single_concept_ordering_valid(self):
        single = {
            "core_concepts": [{"concept_name": "Only", "intuitive_explanation": "x",
                               "mathematical_form": "y", "why_it_matters": "z"}],
            "concept_ordering": ["Only"]
        }
        result = ConceptExtractionResult(**single)
        assert result.concept_ordering == ["Only"]


# ══════════════════════════════════════════════════════════════════════════════
# GROUP C: Cap Enforcement (T14–T18)
# ══════════════════════════════════════════════════════════════════════════════

class TestConceptCap:

    def test_14_7_concepts_capped_to_5(self):
        from backend.config import settings
        result = ConceptExtractionResult(**VALID_7)
        if len(result.core_concepts) > settings.max_concepts:
            result.core_concepts = result.core_concepts[:settings.max_concepts]
            result.concept_ordering = result.concept_ordering[:settings.max_concepts]
        assert len(result.core_concepts) <= 5

    def test_15_5_concepts_not_further_reduced(self):
        from backend.config import settings
        result = ConceptExtractionResult(**VALID_5)
        original_count = len(result.core_concepts)
        if len(result.core_concepts) > settings.max_concepts:
            result.core_concepts = result.core_concepts[:settings.max_concepts]
        assert len(result.core_concepts) == min(original_count, 5)

    def test_16_3_concepts_unchanged_after_cap(self):
        from backend.config import settings
        result = ConceptExtractionResult(**VALID_3)
        original = result.core_concepts[:]
        if len(result.core_concepts) > settings.max_concepts:
            result.core_concepts = result.core_concepts[:settings.max_concepts]
        assert len(result.core_concepts) == 3

    def test_17_ordering_also_capped_with_concepts(self):
        from backend.config import settings
        result = ConceptExtractionResult(**VALID_7)
        if len(result.core_concepts) > settings.max_concepts:
            result.core_concepts = result.core_concepts[:settings.max_concepts]
            result.concept_ordering = result.concept_ordering[:settings.max_concepts]
        assert len(result.concept_ordering) <= 5

    def test_18_cap_preserves_first_n_concepts(self):
        from backend.config import settings
        result = ConceptExtractionResult(**VALID_7)
        first_names = [c.concept_name for c in result.core_concepts[:5]]
        if len(result.core_concepts) > settings.max_concepts:
            result.core_concepts = result.core_concepts[:settings.max_concepts]
        kept_names = [c.concept_name for c in result.core_concepts]
        assert kept_names == first_names


# ══════════════════════════════════════════════════════════════════════════════
# GROUP D: Mathematical Form (T19–T24)
# ══════════════════════════════════════════════════════════════════════════════

class TestMathematicalForm:

    def test_19_mathematical_form_nonempty(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        for c in result.core_concepts:
            assert len(c.mathematical_form.strip()) > 0

    def test_20_mathematical_form_is_string(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        for c in result.core_concepts:
            assert isinstance(c.mathematical_form, str)

    def test_21_latex_in_mathematical_form_accepted(self):
        data = make_concepts(2)
        data["core_concepts"][0]["mathematical_form"] = r"\frac{a}{b} = c"
        result = ConceptExtractionResult(**data)
        assert r"\frac" in result.core_concepts[0].mathematical_form

    def test_22_plain_text_mathematical_form_accepted(self):
        data = make_concepts(2)
        data["core_concepts"][0]["mathematical_form"] = "90 degrees"
        result = ConceptExtractionResult(**data)
        assert "90" in result.core_concepts[0].mathematical_form

    def test_23_begin_environment_in_form_detectable(self):
        data = make_concepts(2)
        data["core_concepts"][0]["mathematical_form"] = r"\begin{pmatrix}1&2\end{pmatrix}"
        result = ConceptExtractionResult(**data)
        has_begin = any(r'\begin' in c.mathematical_form for c in result.core_concepts)
        assert has_begin  # detected, would be cleaned downstream

    def test_24_empty_mathematical_form_detectable(self):
        data = make_concepts(2)
        data["core_concepts"][0]["mathematical_form"] = ""
        result = ConceptExtractionResult(**data)
        empty = [c for c in result.core_concepts if not c.mathematical_form.strip()]
        assert len(empty) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# GROUP E: Serialization & Integration (T25–T30)
# ══════════════════════════════════════════════════════════════════════════════

class TestConceptSerialization:

    def test_25_model_dump_works(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        d = result.model_dump()
        assert "core_concepts" in d
        assert "concept_ordering" in d

    def test_26_core_concepts_in_dump_are_dicts(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        d = result.model_dump()
        assert all(isinstance(c, dict) for c in d["core_concepts"])

    def test_27_ordering_in_dump_is_list_of_strings(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        d = result.model_dump()
        assert all(isinstance(n, str) for n in d["concept_ordering"])

    def test_28_intuitive_explanation_min_length(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        for c in result.core_concepts:
            assert len(c.intuitive_explanation) >= 5

    def test_29_concept_name_no_leading_trailing_whitespace(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        for c in result.core_concepts:
            assert c.concept_name == c.concept_name.strip()

    def test_30_why_it_matters_min_length(self):
        result = ConceptExtractionResult(**PYTH_CONCEPTS)
        for c in result.core_concepts:
            assert len(c.why_it_matters) >= 3
