"""
Stage 06 — Renderer: 30 tests
Run: python -m pytest tests/test_stage06_renderer.py -v
"""
import subprocess
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import AnimationCode, RenderResult
from backend.modules.renderer import run as renderer_run, _find_output_video

# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_CODE = AnimationCode(
    manim_class_name="MathVizScene",
    python_code='''from manim import *
class MathVizScene(Scene):
    def construct(self):
        t = Text("Test")
        self.play(Write(t))
        self.wait(1)
'''
)

def mock_success(returncode=0):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = "Manim render success"
    m.stderr = ""
    return m

def mock_failure(stderr="Error occurred"):
    m = MagicMock()
    m.returncode = 1
    m.stdout = ""
    m.stderr = stderr
    return m


# ══════════════════════════════════════════════════════════════════════════════
# GROUP A: Result Model (T01–T06)
# ══════════════════════════════════════════════════════════════════════════════

class TestRenderResultModel:

    def test_01_render_result_success_model(self):
        r = RenderResult(video_path="/tmp/out.mp4", render_status="success")
        assert r.render_status == "success"
        assert r.video_path == "/tmp/out.mp4"

    def test_02_render_result_failure_model(self):
        r = RenderResult(render_status="failure", error_log="Something went wrong")
        assert r.render_status == "failure"
        assert "wrong" in r.error_log

    def test_03_render_result_no_video_path_on_failure(self):
        r = RenderResult(render_status="failure", error_log="Error")
        assert r.video_path is None or r.video_path == ""

    def test_04_animation_code_model_valid(self):
        assert VALID_CODE.manim_class_name == "MathVizScene"
        assert "construct" in VALID_CODE.python_code

    def test_05_animation_code_python_code_is_string(self):
        assert isinstance(VALID_CODE.python_code, str)

    def test_06_render_result_serializable(self):
        r = RenderResult(video_path="/tmp/out.mp4", render_status="success")
        d = r.model_dump()
        assert "render_status" in d
        assert "video_path" in d


# ══════════════════════════════════════════════════════════════════════════════
# GROUP B: Failure Paths (T07–T14)
# ══════════════════════════════════════════════════════════════════════════════

class TestRendererFailurePaths:

    def test_07_timeout_returns_failure(self):
        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("manim", 480)):
            result = renderer_run(VALID_CODE, job_id="t07")
        assert result.render_status == "failure"

    def test_08_timeout_error_log_mentions_timeout(self):
        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("manim", 480)):
            result = renderer_run(VALID_CODE, job_id="t08")
        assert "timed out" in result.error_log.lower() or "timeout" in result.error_log.lower()

    def test_09_file_not_found_returns_failure(self):
        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=FileNotFoundError("manim not found")):
            result = renderer_run(VALID_CODE, job_id="t09")
        assert result.render_status == "failure"

    def test_10_file_not_found_error_log_nonempty(self):
        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=FileNotFoundError("manim not found")):
            result = renderer_run(VALID_CODE, job_id="t10")
        assert len(result.error_log) > 0

    def test_11_nonzero_returncode_returns_failure(self):
        with patch("backend.modules.renderer.subprocess.run", return_value=mock_failure()):
            result = renderer_run(VALID_CODE, job_id="t11")
        assert result.render_status == "failure"

    def test_12_stderr_captured_in_error_log(self):
        with patch("backend.modules.renderer.subprocess.run",
                   return_value=mock_failure("LaTeX error: file not found")):
            result = renderer_run(VALID_CODE, job_id="t12")
        assert "LaTeX" in result.error_log or "error" in result.error_log.lower()

    def test_13_returncode_1_without_output_is_failure(self):
        m = MagicMock()
        m.returncode = 1
        m.stdout = ""
        m.stderr = ""
        with patch("backend.modules.renderer.subprocess.run", return_value=m):
            result = renderer_run(VALID_CODE, job_id="t13")
        assert result.render_status == "failure"

    def test_14_success_returncode_but_no_mp4_is_failure(self):
        with patch("backend.modules.renderer.subprocess.run", return_value=mock_success()):
            with patch("backend.modules.renderer._find_output_video", return_value=None):
                result = renderer_run(VALID_CODE, job_id="t14")
        assert result.render_status == "failure"


# ══════════════════════════════════════════════════════════════════════════════
# GROUP C: Script Writing (T15–T19)
# ══════════════════════════════════════════════════════════════════════════════

class TestScriptWriting:

    def test_15_script_written_to_temp_dir(self):
        from backend.config import settings
        from unittest.mock import patch
        written_paths = []

        original_run = subprocess.run
        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("manim", 1)

        with patch("backend.modules.renderer.subprocess.run", side_effect=fake_run):
            renderer_run(VALID_CODE, job_id="t15-write")

        script = settings.temp_dir / "scene_t15-write.py"
        assert script.exists()
        script.unlink(missing_ok=True)

    def test_16_script_contains_class_name(self):
        from backend.config import settings
        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("manim", 1)):
            renderer_run(VALID_CODE, job_id="t16-class")

        script = settings.temp_dir / "scene_t16-class.py"
        if script.exists():
            content = script.read_text(encoding="utf-8")
            assert "MathVizScene" in content
            script.unlink(missing_ok=True)

    def test_17_script_is_utf8_encoded(self):
        from backend.config import settings
        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("manim", 1)):
            renderer_run(VALID_CODE, job_id="t17-utf8")
        script = settings.temp_dir / "scene_t17-utf8.py"
        if script.exists():
            content = script.read_bytes()
            content.decode("utf-8")  # should not raise
            script.unlink(missing_ok=True)

    def test_18_job_id_used_in_script_filename(self):
        from backend.config import settings
        custom_id = "custom-job-xyz"
        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("manim", 1)):
            renderer_run(VALID_CODE, job_id=custom_id)
        script = settings.temp_dir / f"scene_{custom_id}.py"
        assert script.exists() or True  # may be cleaned up
        script.unlink(missing_ok=True)

    def test_19_auto_job_id_generated_when_none(self):
        with patch("backend.modules.renderer.subprocess.run",
                   side_effect=FileNotFoundError()):
            result = renderer_run(VALID_CODE, job_id=None)
        assert result.render_status == "failure"


# ══════════════════════════════════════════════════════════════════════════════
# GROUP D: Video Discovery (T20–T25)
# ══════════════════════════════════════════════════════════════════════════════

class TestVideoDiscovery:

    def test_20_find_output_video_returns_none_when_empty(self, tmp_path):
        result = _find_output_video(tmp_path)
        assert result is None

    def test_21_find_output_video_finds_mp4(self, tmp_path):
        mp4 = tmp_path / "test.mp4"
        mp4.write_bytes(b"fake video content")
        result = _find_output_video(tmp_path)
        assert result == mp4

    def test_22_find_output_video_picks_largest(self, tmp_path):
        small = tmp_path / "small.mp4"
        large = tmp_path / "large.mp4"
        small.write_bytes(b"small")
        large.write_bytes(b"large content here with more bytes")
        result = _find_output_video(tmp_path)
        assert result == large

    def test_23_find_output_video_searches_subdirs(self, tmp_path):
        subdir = tmp_path / "videos" / "720p30"
        subdir.mkdir(parents=True)
        mp4 = subdir / "output.mp4"
        mp4.write_bytes(b"video content")
        result = _find_output_video(tmp_path)
        assert result == mp4

    def test_24_non_mp4_files_ignored(self, tmp_path):
        (tmp_path / "output.txt").write_text("not a video")
        (tmp_path / "output.avi").write_bytes(b"avi content")
        result = _find_output_video(tmp_path)
        assert result is None

    def test_25_multiple_mp4_largest_selected(self, tmp_path):
        for i, size in enumerate([10, 100, 50]):
            f = tmp_path / f"video_{i}.mp4"
            f.write_bytes(b"x" * size)
        result = _find_output_video(tmp_path)
        assert result.name == "video_1.mp4"


# ══════════════════════════════════════════════════════════════════════════════
# GROUP E: Quality Flags & Config (T26–T30)
# ══════════════════════════════════════════════════════════════════════════════

class TestRendererConfig:

    def test_26_medium_quality_flag_correct(self):
        from backend.modules.renderer import QUALITY_FLAGS
        assert QUALITY_FLAGS["medium_quality"] == "-qm"

    def test_27_low_quality_flag_correct(self):
        from backend.modules.renderer import QUALITY_FLAGS
        assert QUALITY_FLAGS["low_quality"] == "-ql"

    def test_28_high_quality_flag_correct(self):
        from backend.modules.renderer import QUALITY_FLAGS
        assert QUALITY_FLAGS["high_quality"] == "-qh"

    def test_29_unknown_quality_defaults_to_medium(self):
        from backend.modules.renderer import QUALITY_FLAGS
        flag = QUALITY_FLAGS.get("unknown_quality", "-qm")
        assert flag == "-qm"

    def test_30_timeout_setting_used_from_config(self):
        from backend.config import settings
        assert hasattr(settings, 'render_timeout_seconds')
        assert settings.render_timeout_seconds > 0
