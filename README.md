# VisualAIze V2.0

An LLM-driven pipeline that converts mathematical topics or PDF excerpts into 3Blue1Brown-style animated educational videos — complete with voiceover narration.

## What's New in V2.0

- **Switched from OpenAI to Groq** (free tier, Llama 3.3 70B)
- **RAG system** with ChromaDB — math knowledge base from MATH dataset, GSM8K, DeepMind Mathematics, and curated examples
- **Manim code RAG** — retrieves relevant animation patterns for better rendering
- **TTS narration** via edge-tts (Microsoft Neural voices, completely free)
- **Audio-video merging** via ffmpeg
- **Improved scene quality** — strict layout zones, no overlapping text, clean transitions
- **HTML frontend** as alternative to Streamlit (no executable blocking)

## Features

- Input a math topic or upload a PDF (≤10 pages)
- 6-stage LLM pipeline: Parse → Concepts → Pedagogy → Scenes → Animation → Render
- RAG-enhanced math knowledge base reduces hallucinations
- Auto-generated voiceover narration synced to animations
- Outputs a 2–4 minute educational MP4 video with audio

## Architecture

```
User Input (topic or PDF)
        ↓
   RAG Retrieval (ChromaDB)
        ↓
[1] Parser Agent          — extract definitions, equations, examples
        ↓
[2] Concept Agent         — identify 3-5 core visualizable concepts
        ↓
[3] Pedagogy Agent        — design 5-scene lesson plan (3Blue1Brown style)
        ↓
[4] Scene Generator       — specify Manim objects and animations per scene
        ↓
[5] Animation Agent       — generate Python/Manim code (RAG-assisted)
        ↓
[6] Renderer              — render video via Manim Community
        ↓
[7] Narration Agent       — generate voiceover scripts
        ↓
   edge-tts + ffmpeg      — synthesize audio and merge with video
        ↓
   Final MP4 with Audio
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq API (llama-3.3-70b-versatile) |
| Animation | Manim Community v0.20 |
| Vector DB | ChromaDB + all-MiniLM-L6-v2 |
| TTS | edge-tts (Microsoft Neural) |
| Audio merge | ffmpeg |
| Backend | FastAPI |
| Frontend | Streamlit / HTML |
| LaTeX | MiKTeX |

## Prerequisites

- Python 3.12+
- [Groq API key](https://console.groq.com) (free)
- [Manim Community](https://docs.manim.community/en/stable/installation.html)
- [MiKTeX](https://miktex.org/download) (for LaTeX rendering)
- ffmpeg (for audio merging)

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/ChakriOriginals/VisualAIze.git
cd VisualAIze

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
# source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and fill in your keys
```

## Environment Variables

```env
GROQ_API_KEY
LLM_MODEL=llama-3.3-70b-versatile
MAX_SCENES=5
RENDER_QUALITY=medium_quality
OUTPUT_DIR=./outputs
TEMP_DIR=./tmp
LOG_LEVEL=INFO
TTS_ENABLED=true
TTS_VOICE=en-US-AriaNeural
TTS_SPEAKING_RATE=0.92
```

## Running the App

**Terminal 1 — Backend:**
```bash
python -m uvicorn backend.api.main:app --port 8000
```

**Terminal 2 — Frontend:**
```bash
# Option A: Streamlit
python -m streamlit run frontend/app.py

# Option B: Open test.html directly in browser (no install needed)
start test.html
```

## Populate the RAG Knowledge Base (one time)

```bash
python -m backend.rag.ingest_data
```

This ingests MATH dataset, GSM8K, DeepMind Mathematics, and curated math knowledge into ChromaDB (~9,000 documents).

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate-video` | Run full pipeline |
| `GET` | `/video/{job_id}` | Stream rendered video |
| `GET` | `/docs` | Swagger UI |

## Configuration

Key settings in `backend/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `llm_model` | `llama-3.3-70b-versatile` | Groq model |
| `max_scenes` | `5` | Scenes per video |
| `render_quality` | `medium_quality` | Manim quality flag |
| `render_timeout_seconds` | `480` | Max render time |
| `tts_enabled` | `true` | Enable voiceover |
| `tts_voice` | `en-US-AriaNeural` | TTS voice |

## Project Structure

```
VisualAIze/
├── backend/
│   ├── agents/
│   │   ├── parser_agent.py
│   │   ├── concept_agent.py
│   │   ├── pedagogy_agent.py
│   │   ├── scene_agent.py
│   │   ├── animation_agent.py
│   │   └── narration_agent.py
│   ├── modules/
│   │   ├── renderer.py
│   │   └── tts_generator.py
│   ├── rag/
│   │   ├── retriever.py
│   │   ├── manim_retriever.py
│   │   ├── manim_examples.py
│   │   └── ingest_data.py
│   ├── api/
│   │   └── main.py
│   ├── config.py
│   ├── pipeline.py
│   └── models.py
├── frontend/
│   └── app.py
├── test.html
├── .env.example
├── requirements.txt
└── README.md
```

## Known Limitations

- Groq free tier: 100,000 tokens/day — complex topics may hit limits
- Rendering time: 2–5 minutes on CPU (no GPU required)
- LaTeX rendering requires MiKTeX installed and on system PATH

