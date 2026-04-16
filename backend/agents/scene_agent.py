from __future__ import annotations
import logging
from backend.llm_client import llm_call
from backend.models import PedagogyPlan, SceneInstructionSet, SceneInstruction, ManimObject, ManimAnimation

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a Manim scene architect. Generate precise scene instructions from a pedagogy plan.

SCREEN ZONES (use these exact positions):
  Title   → to_edge(UP, buff=0.2), font_size=36, color=YELLOW
  Content → y between -2.0 and 2.5 (shapes, diagrams, graphs)
  Equation→ move_to([0, -2.8, 0]), font_size=44
  Caption → move_to([0, -3.2, 0]), font_size=24

RULES:
- Max 4 objects visible at once
- Every equation: position = "move_to([0, -2.8, 0])"
- Every title: position = "to_edge(UP, buff=0.2)"
- Every scene MUST end with: FadeOut(*mobjects) run_time=0.8, then wait 0.4
- All positions are 3D: [x, y, 0]

Return JSON:
{
  "scene_instructions": [
    {
      "scene_id": 1,
      "objects": [
        {"obj_id": "title_1", "obj_type": "Text",
         "properties": {"text": "Title", "font_size": 36, "color": "YELLOW",
                        "position": "to_edge(UP, buff=0.2)"}},
        {"obj_id": "eq_1", "obj_type": "MathTex",
         "properties": {"latex": "a^2+b^2=c^2", "font_size": 44,
                        "position": "move_to([0, -2.8, 0])"}}
      ],
      "animations": [
        {"action": "Write",   "target": "title_1",   "duration": 1.2},
        {"action": "wait",    "target": "",           "duration": 1.0},
        {"action": "Write",   "target": "eq_1",       "duration": 2.0},
        {"action": "wait",    "target": "",           "duration": 1.5},
        {"action": "FadeOut", "target": "*mobjects",  "duration": 0.8},
        {"action": "wait",    "target": "",           "duration": 0.4}
      ]
    }
  ]
}
"""

def run(plan: PedagogyPlan) -> SceneInstructionSet:
    scenes_text = []
    for scene in plan.scenes:
        eq_str = "\n".join(f"  - {e}" for e in scene.equations_to_show) if scene.equations_to_show else "  (none)"
        scenes_text.append(
            f"Scene {scene.scene_id}: {scene.scene_title}\n"
            f"Goal: {scene.learning_goal}\n"
            f"Visual metaphor: {scene.visual_metaphor}\n"
            f"Animation strategy: {scene.animation_strategy}\n"
            f"Equations:\n{eq_str}\n"
            f"Duration: ~{scene.estimated_duration_seconds}s"
        )

    user_prompt = (
        "Generate precise scene instructions for this pedagogy plan.\n"
        "Each scene must use the correct screen zones.\n"
        "Equations always at y=-2.8. Titles always at top edge.\n\n"
        + "\n\n".join(scenes_text)
    )

    result = llm_call(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=SceneInstructionSet,
        max_retries=2
    )

    logger.info("Scene instructions generated: %d scenes", len(result.scene_instructions))
    return result