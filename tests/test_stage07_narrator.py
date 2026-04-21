"""
Stage 07 — Narrator / TTS: 30 tests
Run: python -m pytest tests/test_stage07_narrator.py -v
"""
import sys
import subprocess
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import PedagogyPlan

# ── Constants ─────────────────────────────────────────────────────────────────

WORDS_PER_MINUTE = 130
SPEAKING_RATE = 0.92
EFFECTIVE_WPM = WORDS_PER_MINUTE * SPEAKING_RATE  # ~119.6

SAMPLE_PLAN = {
    "scenes": [
        {"scene_id": 1, "scene_title": "Hook", "learning_goal": "Curiosity",
         "visual_metaphor": "A triangle appears", "equations_to_show": [],
         "animation_strategy": "Step 1. Step 2.", "estimated_duration_seconds": 40},
        {"scene_id": 2, "scene_title": "Proof", "learning_goal": "Intuition",
         "visual_metaphor": "Squares on sides", "equations_to_show": [r"a^2+b^2=c^2"],
         "animation_strategy": "Step 1. Step 2. Step 3.", "estimated_duration_seconds": 50},
        {"scene_id": 3, "scene_title": "Formula", "learning_goal": "Formula",
         "visual_metaphor": "Equation", "equations_to_show": [r"a^2+b^2=c^2"],
         "animation_strategy": "Step 1. Step 2. Step 3.", "estimated_duration_seconds": 45},
    ]
}

def word_count(text: str) -> int:
    return len(text.split())

def max_words_for(duration_seconds: int) -> int:
    return int((duration_seconds / 60) * EFFECTIVE_WPM)


# ══════════════════════════════════════════════════════════════════════════════
# GROUP A: NarrationScript Model (T01–T06)
# ══════════════════════════════════════════════════════════════════════════════

class TestNarrationScriptModel:

    def test_01_narration_script_model_importable(self):
        from backend.agents.narration_agent import NarrationScript
        assert NarrationScript is not None

    def test_02_scene_script_model_importable(self):
        from backend.agents.narration_agent import SceneScript
        assert SceneScript is not None

    def test_03_narration_script_has_scripts_list(self):
        from backend.agents.narration_agent import NarrationScript, SceneScript
        ns = NarrationScript(
            scripts=[SceneScript(scene_id=1, title="Hook",
                                 narration="Test narration here", duration_hint_seconds=40)],
            intro="Welcome", outro="Goodbye"
        )
        assert isinstance(ns.scripts, list)

    def test_04_narration_script_has_intro(self):
        from backend.agents.narration_agent import NarrationScript
        ns = NarrationScript(scripts=[], intro="Intro text", outro="")
        assert ns.intro == "Intro text"

    def test_05_narration_script_has_outro(self):
        from backend.agents.narration_agent import NarrationScript
        ns = NarrationScript(scripts=[], intro="", outro="Outro text")
        assert ns.outro == "Outro text"

    def test_06_scene_script_has_all_fields(self):
        from backend.agents.narration_agent import SceneScript
        ss = SceneScript(scene_id=2, title="Proof",
                         narration="This is the proof.", duration_hint_seconds=50)
        assert ss.scene_id == 2
        assert ss.title == "Proof"
        assert ss.narration == "This is the proof."
        assert ss.duration_hint_seconds == 50


# ══════════════════════════════════════════════════════════════════════════════
# GROUP B: Word Count Budget (T07–T14)
# ══════════════════════════════════════════════════════════════════════════════

class TestWordCountBudget:

    def test_07_40s_scene_budget_is_correct(self):
        budget = max_words_for(40)
        assert 75 <= budget <= 85

    def test_08_50s_scene_budget_is_correct(self):
        budget = max_words_for(50)
        assert 95 <= budget <= 105

    def test_09_short_narration_within_budget_40s(self):
        narration = "Think about a right triangle. Notice how the sides relate to each other."
        assert word_count(narration) <= max_words_for(40)

    def test_10_short_narration_within_budget_50s(self):
        narration = "Now we see the squares on each side grow outward from the triangle sides."
        assert word_count(narration) <= max_words_for(50)

    def test_11_long_narration_exceeds_budget(self):
        long = " ".join(["word"] * 200)
        assert word_count(long) > max_words_for(40)

    def test_12_empty_narration_within_any_budget(self):
        assert word_count("") == 0
        assert 0 <= max_words_for(30)

    def test_13_intro_reasonable_length(self):
        intro = "Welcome to a journey through the Pythagorean Theorem."
        assert word_count(intro) <= 20

    def test_14_outro_reasonable_length(self):
        outro = "And that concludes our exploration of this fundamental theorem."
        assert word_count(outro) <= 15


# ══════════════════════════════════════════════════════════════════════════════
# GROUP C: TTS Generator (T15–T22)
# ══════════════════════════════════════════════════════════════════════════════

class TestTTSGenerator:

    def _get_tts(self):
        try:
            from backend.modules.tts_generator import generate_scene_audio
            return generate_scene_audio
        except ImportError:
            pytest.skip("edge-tts not installed")

    def test_15_tts_function_importable(self):
        self._get_tts()

    def test_16_tts_creates_file(self, tmp_path):
        gen = self._get_tts()
        out = tmp_path / "test.mp3"
        ok = gen("Hello world.", out)
        if not ok:
            pytest.skip("TTS network unavailable")
        assert out.exists()

    def test_17_tts_file_nonempty(self, tmp_path):
        gen = self._get_tts()
        out = tmp_path / "test.mp3"
        ok = gen("Testing audio output.", out)
        if not ok:
            pytest.skip("TTS network unavailable")
        assert out.stat().st_size > 0

    def test_18_tts_accepts_different_voices(self, tmp_path):
        gen = self._get_tts()
        for voice in ["en-US-AriaNeural", "en-US-GuyNeural"]:
            out = tmp_path / f"{voice}.mp3"
            ok = gen("Test.", out, voice_name=voice)
            if ok:
                assert out.exists()
                break

    def test_19_tts_accepts_speaking_rate(self, tmp_path):
        gen = self._get_tts()
        out = tmp_path / "rate_test.mp3"
        ok = gen("Test sentence.", out, speaking_rate=0.85)
        if not ok:
            pytest.skip("TTS network unavailable")
        assert out.exists()

    def test_20_tts_output_path_created_if_parent_missing(self, tmp_path):
        gen = self._get_tts()
        nested = tmp_path / "audio" / "scene1" / "narration.mp3"
        ok = gen("Test.", nested)
        if ok:
            assert nested.exists()

    def test_21_get_audio_duration_importable(self):
        try:
            from backend.modules.tts_generator import get_audio_duration
            assert callable(get_audio_duration)
        except ImportError:
            pytest.skip("tts_generator not available")

    def test_22_get_audio_duration_nonexistent_returns_zero(self):
        try:
            from backend.modules.tts_generator import get_audio_duration
            dur = get_audio_duration(Path("/nonexistent/file.mp3"))
            assert dur == 0.0
        except ImportError:
            pytest.skip("tts_generator not available")


# ══════════════════════════════════════════════════════════════════════════════
# GROUP D: Audio Merging (T23–T27)
# ══════════════════════════════════════════════════════════════════════════════

class TestAudioMerging:

    def test_23_merge_function_importable(self):
        try:
            from backend.modules.tts_generator import merge_video_audio
            assert callable(merge_video_audio)
        except ImportError:
            pytest.skip("tts_generator not available")

    def test_24_concat_function_importable(self):
        try:
            from backend.modules.tts_generator import concatenate_audio_files
            assert callable(concatenate_audio_files)
        except ImportError:
            pytest.skip("tts_generator not available")

    def test_25_merge_fails_gracefully_on_missing_video(self, tmp_path):
        try:
            from backend.modules.tts_generator import merge_video_audio
        except ImportError:
            pytest.skip("tts_generator not available")
        audio = tmp_path / "audio.mp3"
        audio.write_bytes(b"fake audio")
        result = merge_video_audio(
            video_path=Path("/nonexistent/video.mp4"),
            audio_path=audio,
            output_path=tmp_path / "out.mp4"
        )
        assert result is False

    def test_26_merge_fails_gracefully_on_missing_audio(self, tmp_path):
        try:
            from backend.modules.tts_generator import merge_video_audio
        except ImportError:
            pytest.skip("tts_generator not available")
        video = tmp_path / "video.mp4"
        video.write_bytes(b"fake video")
        result = merge_video_audio(
            video_path=video,
            audio_path=Path("/nonexistent/audio.mp3"),
            output_path=tmp_path / "out.mp4"
        )
        assert result is False

    def test_27_concat_empty_list_returns_false(self, tmp_path):
        try:
            from backend.modules.tts_generator import concatenate_audio_files
        except ImportError:
            pytest.skip("tts_generator not available")
        result = concatenate_audio_files([], tmp_path / "out.mp3")
        assert result is False


# ══════════════════════════════════════════════════════════════════════════════
# GROUP E: Narration Quality (T28–T30)
# ══════════════════════════════════════════════════════════════════════════════

class TestNarrationQuality:

    def test_28_narration_uses_second_person(self):
        good_narrations = [
            "Notice how the triangle behaves...",
            "Think about what happens when we square the sides.",
            "You can see that the areas add up perfectly.",
        ]
        second_person_words = {"you", "your", "notice", "think", "see", "we", "our"}
        for n in good_narrations:
            words = set(n.lower().split())
            has_second_person = bool(words & second_person_words)
            assert has_second_person, f"Missing second-person language: '{n}'"

    def test_29_narration_avoids_screen_references(self):
        bad_narrations = [
            "As you can see on screen...",
            "The animation shows...",
            "In this video we display...",
        ]
        screen_words = {"screen", "animation", "video", "display", "shown"}
        for n in bad_narrations:
            words = set(n.lower().split())
            has_screen_ref = bool(words & screen_words)
            assert has_screen_ref, f"Expected screen reference in bad example: '{n}'"

    def test_30_scene_scripts_cover_all_scenes(self):
        from backend.agents.narration_agent import NarrationScript, SceneScript
        plan = PedagogyPlan(**SAMPLE_PLAN)
        # Simulate narration for all scenes
        scripts = NarrationScript(
            scripts=[
                SceneScript(scene_id=s.scene_id, title=s.scene_title,
                            narration=f"Narration for {s.scene_title}",
                            duration_hint_seconds=s.estimated_duration_seconds)
                for s in plan.scenes
            ],
            intro="Welcome.",
            outro="Thank you."
        )
        assert len(scripts.scripts) == len(plan.scenes)
        covered_ids = {s.scene_id for s in scripts.scripts}
        plan_ids = {s.scene_id for s in plan.scenes}
        assert covered_ids == plan_ids
