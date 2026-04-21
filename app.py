"""
VisualAIze – Streamlit Frontend
Clean, light-themed UI for generating math animations.
"""

from pathlib import Path

import requests
import streamlit as st

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VisualAIze",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = "http://localhost:8000"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: -apple-system, 'SF Pro Display', 'Inter', BlinkMacSystemFont, sans-serif;
    background-color: #f9f9f7;
    color: #1a1a1a;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px; }

.app-header { text-align: center; padding: 2.5rem 0 1.5rem; }
.app-title {
    font-size: 2.8rem;
    font-weight: 700;
    color: #1a1a1a;
    letter-spacing: -0.03em;
    margin-bottom: 0.4rem;
}
.app-subtitle {
    font-size: 1.05rem;
    color: #6b6b6b;
    margin-bottom: 0;
}
.app-divider {
    border: none;
    border-top: 1px solid #e5e5e5;
    margin: 1.5rem 0;
}

.card-title {
    font-size: 0.72rem;
    font-weight: 600;
    color: #8a8a8a;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.9rem;
}

.badge {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 500;
}
.badge-success { background: #e8f5e9; color: #2e7d32; }
.badge-error   { background: #fdecea; color: #c62828; }

.step-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #f2f2f2;
    font-size: 0.88rem;
}
.step-row:last-child { border-bottom: none; }
.step-name { font-weight: 500; }
.step-desc { color: #8a8a8a; font-size: 0.8rem; }

.stTextArea textarea {
    border-radius: 12px !important;
    border: 1.5px solid #e0e0e0 !important;
    font-family: inherit !important;
    font-size: 0.95rem !important;
    color: #1a1a1a !important;
    background: #fafafa !important;
}
.stTextArea textarea:focus {
    border-color: #1a1a1a !important;
    box-shadow: none !important;
}

.stButton > button {
    background: #1a1a1a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 1.5rem !important;
    font-family: inherit !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    width: 100% !important;
    transition: opacity 0.2s ease !important;
}
.stButton > button:hover { opacity: 0.82 !important; }

.stDownloadButton > button {
    background: #f0f0f0 !important;
    color: #1a1a1a !important;
    border: 1px solid #d0d0d0 !important;
    border-radius: 12px !important;
    font-family: inherit !important;
    font-weight: 500 !important;
}

.stSelectbox label, .stTextArea label, .stFileUploader label {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #4a4a4a !important;
}

video { border-radius: 10px; }

section[data-testid="stSidebar"] {
    background: #f5f5f3;
    border-right: 1px solid #e5e5e5;
}
section[data-testid="stSidebar"] .stButton > button {
    background: #f0f0f0 !important;
    color: #1a1a1a !important;
    border: 1px solid #e0e0e0 !important;
    font-size: 0.85rem !important;
    text-align: left !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #e5e5e5 !important;
    opacity: 1 !important;
}

.stAlert { border-radius: 10px !important; font-size: 0.9rem !important; }
.streamlit-expanderHeader { font-size: 0.85rem !important; color: #6b6b6b !important; }

/* ── FIX: Radio buttons -> clean pill tabs ───────────────────────────────── */
div[data-testid="stRadio"] [role="radiogroup"] {
    display: flex;
    flex-direction: row;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
}

div[data-testid="stRadio"] [role="radiogroup"] > label {
    background: #f4f4f2 !important;
    border: 1px solid #e3e3e3 !important;
    border-radius: 999px !important;
    padding: 0.55rem 0.95rem !important;
    min-height: 42px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    cursor: pointer !important;
    margin: 0 !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
}

/* Hide the default radio circle */
div[data-testid="stRadio"] [role="radiogroup"] > label > div:first-child {
    display: none !important;
}

/* Text spacing inside the pill */
div[data-testid="stRadio"] [role="radiogroup"] > label span {
    font-size: 0.92rem !important;
    font-weight: 500 !important;
}

/* Selected tab */
div[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {
    background: #1a1a1a !important;
    border-color: #1a1a1a !important;
    color: #ffffff !important;
}

/* Selected tab text */
div[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) span {
    color: #ffffff !important;
}

/* Hover state */
div[data-testid="stRadio"] [role="radiogroup"] > label:hover {
    border-color: #bdbdbd !important;
    transform: translateY(-1px);
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="app-header">
    <div class="app-title">VisualAIze</div>
    <div class="app-subtitle">Transform any math concept into a narrated animation</div>
</div>
<hr class="app-divider">
""",
    unsafe_allow_html=True,
)

# ── Layout ────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="large")

STEPS = [
    ("Parsing", "Extracting mathematical content"),
    ("Concepts", "Identifying core concepts"),
    ("Pedagogy", "Designing learning sequence"),
    ("Scenes", "Building animation structure"),
    ("Code", "Writing Manim animation code"),
    ("Rendering", "Rendering video"),
]


def render_steps(active: int) -> str:
    rows = '<div class="card-title">Status</div>'
    for i, (name, desc) in enumerate(STEPS):
        if i < active:
            icon, style = "✅", "color:#2e7d32"
        elif i == active:
            icon, style = "⏳", "color:#f57f17; font-weight:600"
        else:
            icon, style = "○", "color:#c0c0c0"

        rows += f"""
        <div class="step-row" style="{style}">
            <span style="width:1.2rem;text-align:center">{icon}</span>
            <span class="step-name">{name}</span>
            <span class="step-desc">— {desc}</span>
        </div>"""
    return rows


# ── Left: Input ───────────────────────────────────────────────────────────────
with col_left:
    st.markdown('<div class="card-title">Input</div>', unsafe_allow_html=True)

    input_mode = st.radio(
        "mode",
        ["Concept", "Document Upload"],
        horizontal=True,
        label_visibility="collapsed",
    )

    raw_text = ""
    uploaded_file = None

    if input_mode == "Concept":
        raw_text = st.text_area(
            "Topic",
            placeholder="e.g. Pythagorean Theorem\n\nor paste a paragraph from a textbook...",
            height=180,
            label_visibility="collapsed",
        )
    else:
        uploaded_file = st.file_uploader(
            "PDF",
            type=["pdf"],
            help="First 10 pages are processed.",
            label_visibility="collapsed",
        )

    difficulty = st.selectbox("Difficulty", ["High School", "Undergraduate"], index=1)
    difficulty_map = {"High School": "high_school", "Undergraduate": "undergraduate"}

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    generate_clicked = st.button("Generate Animation", use_container_width=True)

# ── Right: Status + Output ────────────────────────────────────────────────────
with col_right:
    status_ph = st.empty()
    progress_ph = st.empty()
    video_ph = st.empty()
    dl_ph = st.empty()

    status_ph.markdown(
        """
        <div class="card-title">Status</div>
        <div style="color:#8a8a8a;font-size:0.9rem;padding:0.4rem 0">
            Enter a topic and click Generate.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Generation logic ──────────────────────────────────────────────────────────
if generate_clicked:
    if not (raw_text.strip() or uploaded_file):
        st.error("Please enter a topic or upload a PDF.")
        st.stop()

    video_ph.empty()
    dl_ph.empty()
    status_ph.markdown(render_steps(0), unsafe_allow_html=True)
    progress_ph.progress(5)

    with st.spinner("Generating — this takes 1–4 minutes..."):
        try:
            if uploaded_file:
                resp = requests.post(
                    f"{API_BASE}/generate-video-from-pdf",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.read(),
                            "application/pdf",
                        )
                    },
                    data={"difficulty_level": difficulty_map[difficulty]},
                    timeout=1200,
                )
            else:
                resp = requests.post(
                    f"{API_BASE}/generate-video",
                    json={
                        "topic_or_text": raw_text,
                        "difficulty_level": difficulty_map[difficulty],
                    },
                    timeout=1200,
                )
        except requests.exceptions.ConnectionError:
            status_ph.empty()
            progress_ph.empty()
            st.error(
                "Cannot reach backend. Run:\n\n`python -m uvicorn backend.api.main:app --port 8000`"
            )
            st.stop()
        except requests.exceptions.Timeout:
            status_ph.empty()
            progress_ph.empty()
            st.error("Request timed out. Try a simpler topic.")
            st.stop()

    progress_ph.progress(100)

    if resp.status_code != 200:
        status_ph.markdown(
            '<div class="badge badge-error">❌ Error</div>',
            unsafe_allow_html=True,
        )
        st.error(f"API error {resp.status_code}: {resp.text}")
        st.stop()

    data = resp.json()

    if data.get("status") == "success":
        status_ph.markdown(
            render_steps(len(STEPS))
            + '<div class="badge badge-success" style="margin-top:0.8rem">✓ Complete</div>',
            unsafe_allow_html=True,
        )

        video_path = data.get("video_path", "")
        job_id = data.get("job_id", "video")

        if video_path and Path(video_path).exists():
            video_bytes = Path(video_path).read_bytes()
            video_ph.video(video_bytes)
            dl_ph.download_button(
                "⬇ Download MP4",
                data=video_bytes,
                file_name=f"VisualAIze_{job_id[:8]}.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
        else:
            st.info(f"Video ready. `GET {API_BASE}/download/{job_id}`")

        trace = data.get("pipeline_trace")
        if trace:
            with st.expander("Debug trace", expanded=False):
                st.json(trace)
    else:
        status_ph.markdown(
            '<div class="badge badge-error">❌ Failed</div>',
            unsafe_allow_html=True,
        )
        st.error(data.get("error", "Unknown error."))
        trace = data.get("pipeline_trace")
        if trace:
            with st.expander("Debug trace", expanded=True):
                st.json(trace)

# ── Sidebar ───────────────────────────────────────────────────────────────────
EXAMPLES = [
    "Pythagorean Theorem",
    "Central Limit Theorem",
    "Fourier Transform",
    "Gradient Descent",
    "Bayes Theorem",
    "Eigenvectors and Eigenvalues",
    "The Derivative as a Limit",
    "Matrix Multiplication",
]

with st.sidebar:
    st.markdown("#### Example Topics")
    st.caption("Click to copy topic")
    for ex in EXAMPLES:
        if st.button(ex, key=f"ex_{ex}"):
            st.info(f"**{ex}**\n\nCopy the text above into the input box.")
    st.markdown("---")
    st.caption(f"Backend: [localhost:8000]({API_BASE}/docs)")