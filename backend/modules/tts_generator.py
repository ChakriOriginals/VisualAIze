"""
TTS generator using edge-tts (Microsoft Edge neural voices).
Completely free, no API key, no billing required.
Uses the same neural voices as Windows 11 / Microsoft Edge browser.
"""
from __future__ import annotations
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


async def _generate_audio_async(script: str, output_path: Path, voice: str, rate: str) -> bool:
    """Async TTS generation using edge-tts."""
    import edge_tts
    try:
        communicate = edge_tts.Communicate(script, voice, rate=rate)
        await communicate.save(str(output_path))
        return True
    except Exception as e:
        logger.error("edge-tts generation failed: %s", e)
        return False


def generate_scene_audio(
    script: str,
    output_path: Path,
    voice_name: str = "en-US-AriaNeural",
    speaking_rate: float = 0.92,
) -> bool:
    try:
        import edge_tts
        import asyncio

        output_path.parent.mkdir(parents=True, exist_ok=True)

        rate_percent = int((speaking_rate - 1.0) * 100)
        rate_str = f"{rate_percent:+d}%"

        async def _generate():
            communicate = edge_tts.Communicate(script, voice_name, rate=rate_str)
            await communicate.save(str(output_path))

        # Fix: handle both cases — running loop (FastAPI) and no loop
        try:
            loop = asyncio.get_running_loop()
            # We're inside FastAPI's event loop — use a thread executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _generate())
                future.result(timeout=30)
        except RuntimeError:
            # No running loop — safe to use asyncio.run()
            asyncio.run(_generate())

        if output_path.exists() and output_path.stat().st_size > 0:
            size_kb = output_path.stat().st_size / 1024
            logger.info("Generated audio: %s (%.1f KB)", output_path.name, size_kb)
            return True
        else:
            logger.error("Audio file not created: %s", output_path)
            return False

    except Exception as e:
        logger.error("TTS generation failed for %s: %s", output_path.name, e)
        return False

def get_audio_duration(audio_path: Path) -> float:
    """Get duration of an audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def concatenate_audio_files(audio_files: List[Path], output_path: Path) -> bool:
    """Concatenate multiple MP3 files into one using ffmpeg."""
    try:
        if not audio_files:
            return False

        if len(audio_files) == 1:
            import shutil
            shutil.copy(audio_files[0], output_path)
            return True

        # Create ffmpeg concat list
        list_file = output_path.parent / "concat_list.txt"
        with open(list_file, "w") as f:
            for af in audio_files:
                f.write(f"file '{af.resolve()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-acodec", "libmp3lame",
            "-q:a", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        list_file.unlink(missing_ok=True)

        if result.returncode != 0:
            logger.error("Audio concat failed: %s", result.stderr[-300:])
            return False

        logger.info("Concatenated %d files -> %s", len(audio_files), output_path.name)
        return True

    except Exception as e:
        logger.error("Audio concatenation error: %s", e)
        return False


def merge_video_audio(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    video_duration: Optional[float] = None,
) -> bool:
    """Merge video and audio. Audio padded/trimmed to match video duration."""
    try:
        if not video_path.exists():
            logger.error("Video not found: %s", video_path)
            return False
        if not audio_path.exists():
            logger.error("Audio not found: %s", audio_path)
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get durations
        if video_duration is None:
            video_duration = get_audio_duration(video_path)
        audio_duration = get_audio_duration(audio_path)

        logger.info("Video: %.1fs | Audio: %.1fs", video_duration, audio_duration)

        if audio_duration > 0 and video_duration > 0:
            if audio_duration < video_duration:
                # Pad audio with silence to match video
                pad = video_duration - audio_duration
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_path),
                    "-i", str(audio_path),
                    "-filter_complex", f"[1:a]apad=pad_dur={pad:.2f}[aout]",
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    str(output_path)
                ]
            else:
                # Trim audio to video length
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_path),
                    "-i", str(audio_path),
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-t", str(video_duration),
                    str(output_path)
                ]
        else:
            # Fallback: simple merge
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(output_path)
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            logger.error("Merge failed: %s", result.stderr[-500:])
            return False

        logger.info("Merged -> %s", output_path.name)
        return True

    except Exception as e:
        logger.error("Merge error: %s", e)
        return False