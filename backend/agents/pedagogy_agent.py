"""
Pedagogy Planner Agent — designs deep, intuition-first lesson plans.
"""
from __future__ import annotations
import logging
from backend.llm_client import llm_call
from backend.models import ConceptExtractionResult, PedagogyPlan
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a world-class math educator designing 3Blue1Brown-style lesson plans.
Every scene must create a genuine "aha moment" — not just present facts.

LESSON DESIGN PHILOSOPHY:
  Scene 1: Hook — surprising question or paradox. NO equations.
  Scene 2: Intuition — concrete visual builds understanding before symbols.
  Scene 3: Reveal — equation emerges naturally from the visual.
  Scene 4: Depth — extend, generalize, or show a non-obvious property.
  Scene 5: Apply — worked numerical example. Real numbers. Verify it works.

SCENE QUALITY STANDARDS — every scene needs ALL of these:
  ✓ Concrete visual metaphor (specific objects, colors, positions)
  ✓ A "before/after" moment where understanding shifts
  ✓ Animation strategy with 4+ numbered steps
  ✓ Equation appears AFTER visual makes it obvious
  ✓ One clear learning goal (single sentence, specific)

ANIMATION STRATEGY FORMAT — use numbered steps:
  Step 1: What appears first, where, what color
  Step 2: What changes or is added next
  Step 3: The KEY visual moment (the insight)
  Step 4: Equation appears at bottom
  Step 5: Caption summarizes in plain English

MANIM-SAFE EQUATION RULES:
  SAFE: a^2 + b^2 = c^2
  SAFE: A \cdot B = C
  SAFE: c_{ij} = \sum_{k=1}^{n} a_{ik} b_{kj}
  SAFE: (A \cdot B) \cdot C = A \cdot (B \cdot C)
  SAFE: A \cdot B \neq B \cdot A
  FORBIDDEN: \begin{pmatrix} (use Matrix() in code instead)
  FORBIDDEN: \begin{bmatrix}
  FORBIDDEN: \text{} inside equations

MATRIX TOPICS SPECIFICALLY:
  - Never use \begin{pmatrix} in equations_to_show
  - Instead write: "A cdot B = C" or "c_{ij} = sum a_{ik} b_{kj}"
  - The Manim code will use Matrix() class to show actual matrices
  - equations_to_show should only contain FORMULA equations, not matrix displays

Return JSON:
{
  "scenes": [
    {
      "scene_id": 1,
      "scene_title": "<5 words max, engaging>",
      "learning_goal": "<one specific thing viewer understands — be precise>",
      "visual_metaphor": "<2-3 sentences describing exact objects, colors, layout, motion>",
      "equations_to_show": [],
      "animation_strategy": "<Step 1: ... Step 2: ... Step 3: ... Step 4: ... Step 5: ...>",
      "estimated_duration_seconds": 45
    }
  ]
}

RULES:
  - Exactly 5 scenes
  - Scene 1: equations_to_show = [] always
  - Scenes 2-3: max 1-2 simple equations, NO \begin{} environments
  - Scene 5: always a specific worked numerical example
  - Duration: 40-60 seconds per scene
  - animation_strategy: at least 5 numbered steps, specific and detailed
"""


def run(
    concepts: ConceptExtractionResult,
    difficulty_level: str = "undergraduate",
    rag_context: str = ""
) -> PedagogyPlan:

    rag_section = (
        f"\n\nKNOWLEDGE BASE (use for accurate equations and visual ideas):\n{rag_context}\n"
        if rag_context else ""
    )

    concept_text = "\n\n".join(
        f"Concept: {c.concept_name}\n"
        f"Explanation: {c.intuitive_explanation}\n"
        f"Math: {c.mathematical_form}\n"
        f"Significance: {c.why_it_matters}"
        for c in concepts.core_concepts
    )

    user_prompt = (
        f"Difficulty: {difficulty_level}"
        f"{rag_section}"
        f"\n\nTeaching order: {', '.join(concepts.concept_ordering)}\n\n"
        f"Concepts:\n{concept_text}\n\n"
        "Design 5 scenes that build genuine intuition step by step.\n"
        "Scene 5 MUST include a specific numerical example with real numbers.\n"
        "IMPORTANT: Do NOT use \\begin{{pmatrix}} in equations_to_show.\n"
        "For matrices, write the formula only (e.g. 'c_{{ij}} = \\sum a_{{ik}} b_{{kj}}')."
    )

    result = llm_call(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=PedagogyPlan,
        max_retries=2,
        max_tokens=2500,
    )

    # Enforce scene count limit
    if len(result.scenes) > settings.max_scenes:
        result.scenes = result.scenes[:settings.max_scenes]

    # Fix scene IDs
    for i, s in enumerate(result.scenes):
        s.scene_id = i + 1

    # Strip any \begin{} from equations — these break Manim LaTeX
    for scene in result.scenes:
        if scene.equations_to_show:
            cleaned = []
            for eq in scene.equations_to_show:
                if r'\begin' in eq or r'\end' in eq:
                    logger.warning("Removed unsafe LaTeX from scene %d: %s", scene.scene_id, eq[:50])
                else:
                    cleaned.append(eq)
            scene.equations_to_show = cleaned

    logger.info("Pedagogy plan: %s", [s.scene_title for s in result.scenes])
    return result