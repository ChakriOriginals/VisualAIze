from __future__ import annotations
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from backend.agents import (
    animation_agent, concept_agent, parser_agent,
    pedagogy_agent, scene_agent
)
from backend.models import (
    AnimationCode, ConceptExtractionResult, GenerateVideoResponse,
    ParsedContent, PedagogyPlan, RenderResult, SceneInstructionSet
)
from backend.modules import math_validator, renderer
from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PipelineTrace:
    parsed_content: Optional[ParsedContent] = None
    concepts: Optional[ConceptExtractionResult] = None
    pedagogy_plan: Optional[PedagogyPlan] = None
    scene_instructions: Optional[SceneInstructionSet] = None
    animation_code: Optional[AnimationCode] = None
    render_result: Optional[RenderResult] = None
    narration_script: Optional[object] = None
    audio_path: Optional[str] = None
    errors: list = field(default_factory=list)


def _add_narration(
    job_id: str,
    pedagogy_plan: PedagogyPlan,
    video_path: str,
    trace: PipelineTrace,
) -> Optional[str]:
    """
    Generate TTS narration and merge with video.
    Returns path to final video with audio, or None if TTS fails.
    Failure is non-fatal — silent video is still returned.
    """
    try:
        from backend.agents import narration_agent
        from backend.modules.tts_generator import (
            generate_scene_audio,
            concatenate_audio_files,
            merge_video_audio,
            get_audio_duration,
        )

        job_dir = Path(settings.output_dir) / job_id
        audio_dir = job_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate narration scripts
        logger.info("[TTS 1/4] Generating narration scripts...")
        narration = narration_agent.run(pedagogy_plan)
        trace.narration_script = narration

        # Step 2: Build full script (intro + scenes + outro)
        all_scripts = []

        if narration.intro:
            all_scripts.append(("intro", narration.intro))

        for script in narration.scripts:
            all_scripts.append((f"scene_{script.scene_id}", script.narration))

        if narration.outro:
            all_scripts.append(("outro", narration.outro))

        # Step 3: Generate audio for each part
        logger.info("[TTS 2/4] Generating audio for %d parts...", len(all_scripts))
        audio_files = []

        for part_name, script_text in all_scripts:
            audio_path = audio_dir / f"{part_name}.mp3"
            success = generate_scene_audio(
                script=script_text,
                output_path=audio_path,
                voice_name=settings.tts_voice,
                speaking_rate=settings.tts_speaking_rate,
            )
            if success and audio_path.exists():
                audio_files.append(audio_path)

        if not audio_files:
            logger.warning("No audio files generated — skipping TTS")
            return None

        # Step 4: Concatenate all audio
        logger.info("[TTS 3/4] Concatenating %d audio segments...", len(audio_files))
        full_audio_path = job_dir / "narration.mp3"
        concat_ok = concatenate_audio_files(audio_files, full_audio_path)

        if not concat_ok or not full_audio_path.exists():
            # Fallback: use first audio file only
            full_audio_path = audio_files[0]

        trace.audio_path = str(full_audio_path)

        # Step 5: Merge video + audio
        logger.info("[TTS 4/4] Merging video and audio...")
        video_path_obj = Path(video_path)
        final_video_path = job_dir / f"{job_id}_with_audio.mp4"

        merge_ok = merge_video_audio(
            video_path=video_path_obj,
            audio_path=full_audio_path,
            output_path=final_video_path,
        )

        if merge_ok and final_video_path.exists():
            logger.info("✅ TTS complete: %s", final_video_path.name)
            return str(final_video_path)
        else:
            logger.warning("Video-audio merge failed — returning silent video")
            return None

    except Exception as e:
        logger.error("TTS pipeline failed (non-fatal): %s", e)
        trace.errors.append(f"TTS failed: {e}")
        return None


def run_pipeline(
    raw_text: str,
    difficulty_level: str = "undergraduate",
    job_id: Optional[str] = None,
    enable_tts: bool = True,
) -> GenerateVideoResponse:

    job_id = job_id or str(uuid.uuid4())
    trace = PipelineTrace()
    logger.info("=== Pipeline START job_id=%s ===", job_id)

    # ── RAG context retrieval ──────────────────────────────────
    rag_context = ""
    try:
        from backend.rag.retriever import retrieve_multi, format_context
        rag_docs = retrieve_multi(
            queries=[raw_text[:200], f"{raw_text[:100]} formula",
                     f"{raw_text[:100]} definition examples"],
            n_per_query=4
        )
        rag_context = format_context(rag_docs, max_chars=2500)
        logger.info("RAG: retrieved %d documents", len(rag_docs))
    except Exception as e:
        logger.warning("RAG retrieval failed, continuing without: %s", e)

    # ── Stage 1: Parser ────────────────────────────────────────
    try:
        logger.info("[1/6] Parser Agent...")
        trace.parsed_content = parser_agent.run(raw_text, difficulty_level, rag_context=rag_context)
    except Exception as exc:
        return GenerateVideoResponse(job_id=job_id, status="failed",
                                     error=f"Parser Agent failed: {exc}")

    # ── Stage 2: Concept Extraction ────────────────────────────
    try:
        logger.info("[2/6] Concept Extraction Agent...")
        trace.concepts = concept_agent.run(trace.parsed_content, difficulty_level, rag_context=rag_context)
        time.sleep(2)  # rate limit buffer
    except Exception as exc:
        return GenerateVideoResponse(job_id=job_id, status="failed",
                                     error=f"Concept Extraction Agent failed: {exc}")

    # ── Stage 3: Pedagogy Planner ──────────────────────────────
    try:
        logger.info("[3/6] Pedagogy Planner Agent...")
        trace.pedagogy_plan = pedagogy_agent.run(trace.concepts, difficulty_level, rag_context=rag_context)
        time.sleep(2)
    except Exception as exc:
        return GenerateVideoResponse(job_id=job_id, status="failed",
                                     error=f"Pedagogy Planner Agent failed: {exc}")

    for scene in trace.pedagogy_plan.scenes:
        if scene.equations_to_show:
            scene.equations_to_show = math_validator.filter_valid_equations(scene.equations_to_show)

    # ── Stage 4: Scene Generator ───────────────────────────────
    try:
        logger.info("[4/6] Scene Generator Agent...")
        trace.scene_instructions = scene_agent.run(trace.pedagogy_plan)
        time.sleep(2)
    except Exception as exc:
        return GenerateVideoResponse(job_id=job_id, status="failed",
                                     error=f"Scene Generator Agent failed: {exc}")

    # ── Stage 5: Animation Code Generator ─────────────────────
    try:
        logger.info("[5/6] Animation Code Generator Agent...")
        trace.animation_code = animation_agent.run(trace.scene_instructions, trace.pedagogy_plan)
    except ValueError as exc:
        return GenerateVideoResponse(job_id=job_id, status="failed",
                                     error=f"Animation Code Generator produced invalid code: {exc}")
    except Exception as exc:
        return GenerateVideoResponse(job_id=job_id, status="failed",
                                     error=f"Animation Code Generator failed: {exc}")

    # ── Stage 6: Renderer ──────────────────────────────────────
    try:
        logger.info("[6/6] Renderer...")
        trace.render_result = renderer.run(trace.animation_code, job_id=job_id)
    except Exception as exc:
        return GenerateVideoResponse(job_id=job_id, status="failed",
                                     error=f"Renderer crashed: {exc}")

    if trace.render_result.render_status == "failure":
        return GenerateVideoResponse(
            job_id=job_id, status="failed",
            error=f"Manim render failed:\n{trace.render_result.error_log}",
            pipeline_trace=_trace_to_dict(trace)
        )

    # ── Stage 7: TTS Narration (optional) ─────────────────────
    final_video_path = trace.render_result.video_path
    tts_enabled = enable_tts and settings.tts_enabled

    if tts_enabled and final_video_path:
        logger.info("[7/7] TTS Narration...")
        narrated_path = _add_narration(
            job_id=job_id,
            pedagogy_plan=trace.pedagogy_plan,
            video_path=final_video_path,
            trace=trace,
        )
        if narrated_path:
            final_video_path = narrated_path
            logger.info("Final video with narration: %s", final_video_path)
        else:
            logger.warning("TTS failed — returning silent video")
    else:
        logger.info("TTS disabled — returning silent video")

    logger.info("=== Pipeline COMPLETE job_id=%s ===", job_id)
    return GenerateVideoResponse(
        job_id=job_id,
        status="success",
        video_path=final_video_path,
        pipeline_trace=_trace_to_dict(trace)
    )


def _trace_to_dict(trace: PipelineTrace) -> dict:
    result = {
        "parsed_content": trace.parsed_content.model_dump() if trace.parsed_content else None,
        "concepts": trace.concepts.model_dump() if trace.concepts else None,
        "pedagogy_plan": trace.pedagogy_plan.model_dump() if trace.pedagogy_plan else None,
        "animation_code": {
            "class_name": trace.animation_code.manim_class_name,
            "lines": len(trace.animation_code.python_code.splitlines())
        } if trace.animation_code else None,
        "render_result": trace.render_result.model_dump() if trace.render_result else None,
        "audio_path": trace.audio_path,
    }
    if trace.narration_script:
        try:
            result["narration_script"] = trace.narration_script.model_dump()
        except Exception:
            pass
    return result