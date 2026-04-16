"""
Narration Script Generator Agent.
Generates natural, well-paced voiceover scripts timed to match animations.
"""
from __future__ import annotations
import logging
from backend.llm_client import llm_call
from backend.models import PedagogyPlan
from pydantic import BaseModel, Field
from typing import List

logger = logging.getLogger(__name__)


class SceneScript(BaseModel):
    scene_id: int
    title: str
    narration: str
    duration_hint_seconds: int = 40


class NarrationScript(BaseModel):
    scripts: List[SceneScript]
    intro: str = ""
    outro: str = ""


SYSTEM_PROMPT = """
You are an expert math educator and narrator — think Khan Academy meets 3Blue1Brown.
Write voiceover scripts that feel natural when spoken aloud, not when read.

CORE RULES:
1. SPEAK TO THE VIEWER directly: "Notice...", "Think about...", "Here's the key..."
2. BUILD INTUITION before formulas — explain WHY something works
3. USE PAUSES: write "..." where the viewer needs a moment to absorb
4. COMPLEMENT VISUALS — add insight the animation cannot show
5. NEVER say: "as you can see", "on screen", "in this animation", "the video shows"
6. SHORT SENTENCES — average 8-12 words per sentence when spoken
7. MATCH DURATION — calculate words carefully (140 words = 60 seconds at normal pace)

WORD COUNT GUIDE (at 0.92x speaking rate, ~130 words/minute):
  35s scene →  75 words max
  40s scene →  87 words max
  45s scene → 100 words max
  50s scene → 108 words max
  55s scene → 119 words max
  60s scene → 130 words max

GOOD NARRATION EXAMPLE (Matrix Multiplication):
"A matrix is simply a grid of numbers... organized in rows and columns.
Think of it like a spreadsheet. Each number has an exact address — its row and column.
This organization isn't just for neatness. It unlocks a powerful way to combine information.
When we multiply two matrices... we're combining their information in a very specific way.
Each entry in the result comes from a row of the first matrix... and a column of the second.
It's like a dot product — multiply matching pairs, then add them up."

BAD NARRATION (avoid):
"As you can see on the screen, matrix A and matrix B appear. The elements are highlighted.
The resulting matrix C is shown on the right side of the animation."

PACING MARKERS — use these in scripts:
  "..." = half-second pause (let visual sink in)
  Short sentences = natural rhythm
  Questions = engage viewer ("Why does this work?")
  "Notice that..." = draw attention

INTRO: 1-2 sentences. Set curiosity. No equations.
OUTRO: 1-2 sentences. Connect to real world. Inspiring.

Return JSON ONLY:
{
  "intro": "Engaging 1-2 sentence welcome (no equations)",
  "scripts": [
    {
      "scene_id": 1,
      "title": "Scene Title",
      "narration": "Natural spoken script matching duration...",
      "duration_hint_seconds": 45
    }
  ],
  "outro": "Inspiring 1-2 sentence close connecting to real applications"
}
"""


def run(plan: PedagogyPlan) -> NarrationScript:
    """Generate voiceover scripts for all scenes."""

    scenes_text = []
    for scene in plan.scenes:
        eq_list = [e for e in scene.equations_to_show
                   if r'\begin' not in e] if scene.equations_to_show else []
        eq_str = ", ".join(eq_list) if eq_list else "none"

        scenes_text.append(
            f"Scene {scene.scene_id}: {scene.scene_title}\n"
            f"Goal: {scene.learning_goal}\n"
            f"Visual: {scene.visual_metaphor}\n"
            f"Strategy: {scene.animation_strategy[:200]}\n"
            f"Key equations: {eq_str}\n"
            f"Duration: {scene.estimated_duration_seconds}s "
            f"(max {int(scene.estimated_duration_seconds * 130 / 60)} words)"
        )

    main_topic = plan.scenes[0].scene_title if plan.scenes else "Mathematics"

    user_prompt = (
        f"Write voiceover narration for this math lesson on: {main_topic}\n\n"
        f"Scenes:\n\n" + "\n\n".join(scenes_text) + "\n\n"
        "Write as if speaking to a curious student. Build intuition. Use pauses (...).\n"
        "Stay within the word count limits for each scene duration.\n"
        "NEVER mention the animation, screen, or video."
    )

    result = llm_call(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=NarrationScript,
        max_retries=2,
        max_tokens=2000,
    )

    logger.info("Narration generated: %d scenes + intro + outro", len(result.scripts))
    return result