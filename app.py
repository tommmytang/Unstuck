import streamlit as st
import os
import json
import cohere
from tavily import TavilyClient

COHERE_KEY = os.getenv("COHERE_API_KEY", "KYrrefNlqXGEs6hZzaX0mSqyrW7EYLfBmhdB7YVA")
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "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")

MAX_QUESTIONS = 3
MODEL_NAME = "command-a-03-2025"

co = cohere.Client(COHERE_KEY)
tavily = TavilyClient(api_key=TAVILY_KEY)

# ── Session state init ────────────────────────────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "splash"
    st.session_state.chat_history = []
    st.session_state.question_count = 0
    st.session_state.products = []
    st.session_state.factors = ""
    st.session_state.factors_list = []
    st.session_state.ranked_factors = []

def ask_cohere(prompt, temp=0.3):
    response = co.chat(
        message=prompt,
        chat_history=st.session_state.chat_history,
        model=MODEL_NAME,
        temperature=temp
    )
    return response.text

st.set_page_config(
    page_title="Unstuck",
    page_icon="◦",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400;1,500&family=DM+Sans:wght@200;300;400;500&family=Martian+Mono:wght@300;400&display=swap');

:root {
    --paper:       #F7F4EE;
    --paper-warm:  #F0EBE1;
    --paper-deep:  #E8E2D6;
    --ink:         #141210;
    --ink-mid:     #2E2B24;
    --ink-soft:    #6B6559;
    --ink-ghost:   #A89F93;
    --rule:        #D4CEC4;
    --rule-light:  #E4DFDA;
    --accent:      #141210;
    --gold:        #8C7A5E;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stStatusWidget"] { display: none; }

/* ── Page background with fine grain ── */
.stApp {
    background-color: var(--paper) !important;
    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E") !important;
}

/* ── Layout ── */
.block-container {
    max-width: 680px !important;
    padding: 4.5rem 2.5rem 8rem !important;
    margin: 0 auto !important;
}

/* ── Masthead ── */
.masthead {
    padding-bottom: 3rem;
    margin-bottom: 3.5rem;
    position: relative;
}
.masthead::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(to right, var(--ink) 0%, var(--ink) 30%, transparent 100%);
}
.masthead-eyebrow {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.58rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--gold);
    margin: 0 0 1.4rem;
    font-weight: 300;
}
.masthead-title {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-size: 6rem;
    font-weight: 300;
    line-height: 0.92;
    color: var(--ink);
    margin: 0 0 1rem;
    letter-spacing: -0.02em;
}
.masthead-title em {
    font-style: italic;
    font-weight: 300;
    color: var(--ink-soft);
}
.masthead-sub {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem;
    color: var(--ink-ghost);
    font-weight: 300;
    margin: 0;
    letter-spacing: 0.04em;
}

/* ── Phase strip ── */
.phase-strip {
    display: flex;
    align-items: flex-end;
    gap: 0;
    margin-bottom: 3.5rem;
    border-bottom: 1px solid var(--rule-light);
}
.phase-item {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.56rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--rule);
    padding: 0 2rem 0.85rem 0;
    position: relative;
    font-weight: 300;
    white-space: nowrap;
    transition: color 0.2s;
}
.phase-item.active { color: var(--ink); }
.phase-item.active::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 100%;
    height: 2px;
    background: var(--ink);
}
.phase-item.done {
    color: var(--ink-ghost);
}
.phase-item.done::before {
    content: '✓ ';
    font-size: 0.5rem;
}

/* ── Section label ── */
.section-label {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.56rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--gold);
    display: block;
    margin-bottom: 1.5rem;
    font-weight: 300;
}
.section-rule {
    border: none;
    border-top: 1px solid var(--rule-light);
    margin: 2.5rem 0;
}

/* ── Info band ── */
.info-band {
    padding: 1.25rem 1.5rem;
    margin-bottom: 2rem;
    background: var(--paper-warm);
    border-left: 2px solid var(--ink);
    position: relative;
}
.info-band strong {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.52rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--gold);
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 300;
}
.info-band p {
    font-size: 0.9rem;
    color: var(--ink-mid);
    margin: 0;
    line-height: 1.65;
    font-weight: 300;
}

/* ── Body text ── */
.body-text {
    font-size: 0.9rem;
    color: var(--ink-soft);
    line-height: 1.75;
    font-weight: 300;
    margin-bottom: 2rem;
    letter-spacing: 0.01em;
}

/* ── Drag-rank widget ── */
.rank-list {
    list-style: none;
    padding: 0;
    margin: 0 0 2rem;
}
.rank-item {
    display: flex;
    align-items: center;
    gap: 1.1rem;
    padding: 1rem 1.2rem;
    margin-bottom: 2px;
    border: 1px solid var(--rule-light);
    border-left: 2px solid transparent;
    cursor: grab;
    user-select: none;
    transition: border-color 0.15s, background 0.15s, transform 0.1s;
    background: var(--paper);
}
.rank-item:hover {
    background: var(--paper-warm);
    border-left-color: var(--ink-ghost);
}
.rank-item:active { cursor: grabbing; }
.rank-item.dragging {
    opacity: 0.35;
    transform: scale(0.98);
}
.rank-item.drag-over {
    border-left-color: var(--ink);
    background: var(--paper-warm);
}
.rank-badge {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 1.3rem;
    font-weight: 300;
    min-width: 1.5rem;
    text-align: center;
    flex-shrink: 0;
    line-height: 1;
}
.rank-handle {
    font-size: 0.65rem;
    color: var(--rule);
    letter-spacing: 0.03em;
    flex-shrink: 0;
    line-height: 1;
}
.rank-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    font-weight: 300;
    flex: 1;
    color: var(--ink-mid);
    letter-spacing: 0.01em;
}
.rank-importance {
    font-family: 'Martian Mono', monospace;
    font-size: 0.54rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    flex-shrink: 0;
    font-weight: 300;
}

/* ── Choice cards ── */
.choice-card {
    padding: 1.6rem 1.75rem;
    background: var(--paper);
    border: 1px solid var(--rule-light);
    border-top: none;
    margin-bottom: 0;
    transition: background 0.15s;
    position: relative;
}
.choice-card:first-of-type {
    border-top: 1px solid var(--rule-light);
}
.choice-card:hover {
    background: var(--paper-warm);
}
.choice-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1.5rem;
    margin-bottom: 0.6rem;
}
.choice-card-meta {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    flex: 1;
    min-width: 0;
}
.choice-rank {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.54rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--gold);
    display: block;
}
.choice-name {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.35rem;
    font-weight: 400;
    color: var(--ink);
    margin: 0;
    line-height: 1.15;
    letter-spacing: -0.01em;
}
.choice-price {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.78rem;
    color: var(--ink-mid);
    font-weight: 300;
    letter-spacing: 0.02em;
    white-space: nowrap;
    flex-shrink: 0;
    padding-top: 0.15rem;
}
.choice-reason {
    font-family: 'Cormorant Garamond', serif !important;
    font-style: italic;
    font-size: 0.95rem;
    color: var(--ink-soft);
    line-height: 1.6;
    margin: 0 0 1rem;
    font-weight: 300;
}
.choice-details {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--rule-light);
}
.choice-detail-row {
    display: flex;
    gap: 0.75rem;
    font-size: 0.82rem;
    line-height: 1.5;
    font-weight: 300;
    color: var(--ink-mid);
}
.choice-detail-label {
    font-family: 'Martian Mono', monospace;
    font-size: 0.5rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--ink-ghost);
    white-space: nowrap;
    margin-top: 0.15rem;
    flex-shrink: 0;
    min-width: 6.5rem;
}
.choice-stats {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
}
.stat-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}
.stat-label {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.5rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--ink-ghost);
    font-weight: 300;
}
.stat-value {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.84rem;
    color: var(--ink-mid);
    font-weight: 300;
}

/* ── Deal rows ── */
.deal-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 0;
    border-bottom: 1px solid var(--rule-light);
    gap: 1.5rem;
    transition: opacity 0.15s;
}
.deal-row:hover { opacity: 0.75; }
.deal-title {
    font-size: 0.84rem;
    color: var(--ink-mid);
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 300;
}
.deal-link {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    color: var(--ink-soft);
    text-decoration: none;
    white-space: nowrap;
    flex-shrink: 0;
    padding: 0.4rem 0.9rem;
    border: 1px solid var(--rule);
    transition: all 0.15s;
}
.deal-link:hover {
    color: var(--paper);
    background: var(--ink);
    border-color: var(--ink);
    text-decoration: none;
}

/* ── Closing ── */
.closing {
    padding-top: 2rem;
    font-family: 'Cormorant Garamond', serif !important;
    font-style: italic;
    font-size: 1.1rem;
    font-weight: 300;
    color: var(--ink-soft);
    line-height: 1.65;
}

/* ── Inputs ── */
[data-testid="stTextInput"] > div,
[data-testid="stTextInput"] > div > div {
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    background: transparent !important;
}
[data-testid="stTextInput"] input {
    border: none !important;
    border-bottom: 1px solid var(--rule) !important;
    border-radius: 0 !important;
    padding: 0.75rem 0 !important;
    box-shadow: none !important;
    background: transparent !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    color: var(--ink) !important;
    font-weight: 300 !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stTextInput"] input:focus {
    border-bottom: 1px solid var(--ink) !important;
    box-shadow: none !important;
    outline: none !important;
    background: transparent !important;
}
[data-testid="stTextInput"] input::placeholder { color: var(--rule) !important; }
[data-testid="stTextInput"] label p {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.54rem !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    color: var(--ink-ghost) !important;
    font-weight: 300 !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
    border: none !important;
    border-bottom: 1px solid var(--rule) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    background: transparent !important;
}
[data-testid="stChatInput"] textarea {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    font-weight: 300 !important;
    color: var(--ink) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--ink-ghost) !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.5rem 0 !important;
}
[data-testid="stChatMessageContent"] p {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    line-height: 1.75 !important;
    color: var(--ink-soft) !important;
    font-weight: 300 !important;
}
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"] { display: none !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 1px solid var(--rule) !important;
    padding-left: 1.25rem !important;
    margin-left: 2.5rem !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 2px solid var(--ink) !important;
    padding-left: 1.25rem !important;
}

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    color: var(--ink) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.62rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 2.25rem !important;
    box-shadow: none !important;
    transition: background 0.2s, color 0.2s !important;
    margin-top: 1.5rem !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    background: var(--ink) !important;
    color: var(--paper) !important;
    box-shadow: none !important;
}
.stButton > button:focus {
    box-shadow: none !important;
    outline: none !important;
}

/* ── Form submit button ── */
[data-testid="stFormSubmitButton"] > button {
    background: transparent !important;
    color: var(--ink) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 0 !important;
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.62rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 2.25rem !important;
    box-shadow: none !important;
    transition: background 0.2s, color 0.2s !important;
    margin-top: 1.5rem !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--ink) !important;
    color: var(--paper) !important;
    box-shadow: none !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] p {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--ink-ghost) !important;
}

/* ── Error / info boxes ── */
[data-testid="stAlert"] {
    border-radius: 0 !important;
    border-left: 2px solid var(--ink) !important;
    background: var(--paper-warm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.84rem !important;
    font-weight: 300 !important;
}

/* ── Columns ── */
[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
}

/* ── Splash page ── */
.splash-hero {
    padding: 3rem 0 4rem;
    border-bottom: 1px solid var(--rule-light);
    margin-bottom: 3.5rem;
}
.splash-title {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-size: 7.5rem;
    font-weight: 300;
    line-height: 0.88;
    color: var(--ink);
    margin: 1.2rem 0 1.6rem;
    letter-spacing: -0.025em;
}
.splash-title em {
    font-style: italic;
    color: var(--ink-soft);
}
.splash-deck {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.25rem;
    font-weight: 300;
    font-style: italic;
    color: var(--ink-soft);
    line-height: 1.55;
    margin: 0;
    max-width: 480px;
}
.splash-divider {
    height: 1px;
    background: linear-gradient(to right, var(--rule) 0%, transparent 80%);
    margin: 2rem 0;
}
.splash-how-label {
    font-family: 'Martian Mono', monospace !important;
    font-size: 0.54rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 2rem;
    font-weight: 300;
}
.splash-steps {
    display: flex;
    flex-direction: column;
    gap: 0;
}
.splash-step {
    display: flex;
    gap: 2rem;
    align-items: flex-start;
    padding: 1.5rem 0;
    border-bottom: 1px solid var(--rule-light);
}
.splash-step:first-child {
    border-top: 1px solid var(--rule-light);
}
.splash-step-num {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 1.5rem;
    font-weight: 300;
    color: var(--ink-ghost);
    min-width: 1.75rem;
    line-height: 1.2;
    padding-top: 0.1rem;
    flex-shrink: 0;
}
.splash-step-body {
    flex: 1;
    min-width: 0;
}
.splash-step-title {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem;
    font-weight: 400;
    color: var(--ink);
    margin-bottom: 0.4rem;
    letter-spacing: 0.01em;
}
.splash-step-desc {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem;
    font-weight: 300;
    color: var(--ink-soft);
    line-height: 1.7;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

# Inject JS to make Enter submit forms / click primary buttons
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if (e.key !== 'Enter') return;
    const active = document.activeElement;
    if (!active) return;
    const tag = active.tagName && active.tagName.toLowerCase();
    // If user is in a textarea and wants a newline (Shift+Enter), do nothing
    if (tag === 'textarea' && e.shiftKey) return;

    // Try to submit the nearest form (Streamlit forms)
    const form = active.closest && active.closest('form');
    if (form) {
        // Prefer requestSubmit when available so native submit handlers run
        if (typeof form.requestSubmit === 'function') {
            form.requestSubmit();
        } else {
            // Fallback: find a submit button inside the form
            const submitBtn = form.querySelector('button[type="submit"]') || form.querySelector('button');
            if (submitBtn) submitBtn.click();
        }
        e.preventDefault();
        return;
    }

    // Otherwise, find the first visible Streamlit action button and click it
    const buttons = Array.from(document.querySelectorAll('.stButton > button'));
    for (const btn of buttons) {
        const style = window.getComputedStyle(btn);
        if (style.display === 'none' || style.visibility === 'hidden' || btn.disabled) continue;
        btn.click();
        e.preventDefault();
        return;
    }
});
</script>
""", unsafe_allow_html=True)

# ── Masthead (shown on all phases except splash) ──────────────────────────────
if st.session_state.phase != "splash":
    st.markdown("""
    <div class="masthead">
        <p class="masthead-eyebrow">Shopping Intelligence — Vol. I</p>
        <p class="masthead-title">Un<em>stuck.</em></p>
        <p class="masthead-sub">Stop deliberating. Let the research happen.</p>
    </div>
    """, unsafe_allow_html=True)

# ── Phase strip ───────────────────────────────────────────────────────────────
_phase_order  = ["splash", "intake_target", "intake_questions", "curation", "ranking", "scoring", "choice", "deals"]
_phase_labels = {
    "splash":           "I — Diagnosis",
    "intake_target":    "I — Diagnosis",
    "intake_questions": "I — Diagnosis",
    "curation":         "II — Search",
    "ranking":          "III — Ranking",
    "scoring":          "IV — Results",
    "choice":           "IV — Results",
    "deals":            "V — Deals",
}
_done_labels = ["I — Diagnosis", "II — Search", "III — Ranking", "IV — Results", "V — Deals"]

def render_phase_strip(current):
    active_label = _phase_labels[current]
    strips, seen = [], set()
    for p in _phase_order:
        lbl = _phase_labels[p]
        if lbl in seen:
            continue
        seen.add(lbl)
        if lbl == active_label:
            cls = "active"
        elif _done_labels.index(lbl) < _done_labels.index(active_label):
            cls = "done"
        else:
            cls = ""
        strips.append(f'<span class="phase-item {cls}">{lbl}</span>')
    st.markdown(f'<div class="phase-strip">{"".join(strips)}</div>', unsafe_allow_html=True)


# ── Drag-rank component ───────────────────────────────────────────────────────
def render_drag_rank(factors_list):
    """
    Renders a drag-and-drop ranking widget via HTML/JS.
    Returns the current order stored in session_state.ranked_factors.
    Uses a hidden Streamlit text_input as the bridge to capture the result.
    """
    if not st.session_state.ranked_factors:
        st.session_state.ranked_factors = factors_list[:]

    # Accent colors: most important = near-ink, least = near-rule
    accent_colors = ["#141210", "#6B6559", "#A89F93", "#D4CEC4"]
    importance_labels = ["Most important", "Important", "Less important", "Least important"]

    items_json = json.dumps(st.session_state.ranked_factors)

    drag_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;1,300&family=DM+Sans:wght@300;400&family=Martian+Mono:wght@300&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    font-family: 'DM Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  ul {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}
  li.rank-item {{
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.95rem 1.2rem;
    margin-bottom: 3px;
    border: 1px solid #E4DFDA;
    border-left: 2px solid transparent;
    cursor: grab;
    user-select: none;
    transition: border-color 0.15s, background 0.15s, transform 0.1s;
    background: #F7F4EE;
  }}
  li.rank-item:hover {{
    background: #F0EBE1;
    border-left-color: #A89F93;
  }}
  li.rank-item:active {{ cursor: grabbing; }}
  li.rank-item.dragging {{
    opacity: 0.3;
    transform: scale(0.98);
  }}
  li.rank-item.drag-over {{
    border-left-color: #141210;
    background: #F0EBE1;
  }}
  .rank-handle {{
    font-size: 0.7rem;
    color: #D4CEC4;
    letter-spacing: 0.05em;
    flex-shrink: 0;
    line-height: 1;
  }}
  .rank-badge {{
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 1.25rem;
    font-weight: 300;
    min-width: 1.4rem;
    text-align: center;
    flex-shrink: 0;
    line-height: 1;
  }}
  .rank-label {{
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    font-weight: 300;
    flex: 1;
    color: #2E2B24;
    letter-spacing: 0.01em;
  }}
  .rank-importance {{
    font-family: 'Martian Mono', monospace;
    font-size: 0.52rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    flex-shrink: 0;
    font-weight: 300;
  }}
</style>
</head>
<body>
<ul id="rank-list"></ul>
<input type="hidden" id="rank-output" value="" />
<script>
(function() {{
  const factors = {items_json};
  const accentColors = {json.dumps(accent_colors)};
  const importanceLabels = {json.dumps(importance_labels)};
  const list = document.getElementById('rank-list');

  function buildList(items) {{
    list.innerHTML = '';
    items.forEach((factor, i) => {{
      const li = document.createElement('li');
      li.className = 'rank-item';
      li.draggable = true;
      li.dataset.index = i;
      li.innerHTML =
        '<span class="rank-handle">⠶⠶</span>' +
        '<span class="rank-badge" style="color:' + accentColors[i] + '">' + (i + 1) + '</span>' +
        '<span class="rank-label">' + factor + '</span>' +
        '<span class="rank-importance" style="color:' + accentColors[i] + '">' + importanceLabels[i] + '</span>';
      li.addEventListener('dragstart', onDragStart);
      li.addEventListener('dragover', onDragOver);
      li.addEventListener('drop', onDrop);
      li.addEventListener('dragend', onDragEnd);
      list.appendChild(li);
    }});
  }}

  let dragSrc = null;
  let currentOrder = [...factors];

  function onDragStart(e) {{
    dragSrc = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
  }}
  function onDragOver(e) {{
    e.preventDefault();
    document.querySelectorAll('.rank-item').forEach(el => el.classList.remove('drag-over'));
    this.classList.add('drag-over');
    e.dataTransfer.dropEffect = 'move';
  }}
  function onDrop(e) {{
    e.preventDefault();
    if (dragSrc === this) return;
    const allItems = [...list.querySelectorAll('.rank-item')];
    const fromIdx = allItems.indexOf(dragSrc);
    const toIdx = allItems.indexOf(this);
    const moved = currentOrder.splice(fromIdx, 1)[0];
    currentOrder.splice(toIdx, 0, moved);
    buildList(currentOrder);
    document.getElementById('rank-output').value = currentOrder.join(', ');
    const stInput = window.parent.document.querySelector('input[aria-label="ranked_factors_bridge"]');
    if (stInput) {{
      stInput.value = currentOrder.join(', ');
      stInput.dispatchEvent(new Event('input', {{bubbles: true}}));
    }}
  }}
  function onDragEnd() {{
    document.querySelectorAll('.rank-item').forEach(el => {{
      el.classList.remove('dragging');
      el.classList.remove('drag-over');
    }});
  }}

  buildList(currentOrder);
}})();
</script>
</body>
</html>
"""
    st.components.v1.html(drag_html, height=len(factors_list) * 72 + 20, scrolling=False)


# ── Phase: splash ────────────────────────────────────────────────────────────
if st.session_state.phase == "splash":
    st.markdown("""
    <div class="splash-hero">
        <p class="masthead-eyebrow">Shopping Intelligence — Vol. I</p>
        <h1 class="splash-title">Un<em>stuck.</em></h1>
        <p class="splash-deck">You've been thinking about buying it for weeks.<br>We'll end that in five minutes.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="splash-divider"></div>
    <p class="splash-how-label">How it works</p>
    <div class="splash-steps">
        <div class="splash-step">
            <span class="splash-step-num">I</span>
            <div class="splash-step-body">
                <p class="splash-step-title">Tell us what you're after</p>
                <p class="splash-step-desc">Name the thing. As vague or specific as you like. We'll ask two or three quick questions to understand what actually matters to you.</p>
            </div>
        </div>
        <div class="splash-step">
            <span class="splash-step-num">II</span>
            <div class="splash-step-body">
                <p class="splash-step-title">We search the web for you</p>
                <p class="splash-step-desc">Real-time search across reviews, comparisons, and retailer listings — distilled into five strong candidates.</p>
            </div>
        </div>
        <div class="splash-step">
            <span class="splash-step-num">III</span>
            <div class="splash-step-body">
                <p class="splash-step-title">Rank what matters most</p>
                <p class="splash-step-desc">Drag four factors into your order of priority. Price first? Build quality? We score each option against your ranking.</p>
            </div>
        </div>
        <div class="splash-step">
            <span class="splash-step-num">IV</span>
            <div class="splash-step-body">
                <p class="splash-step-title">Get your top three — and the best deal</p>
                <p class="splash-step-desc">A scored shortlist with the reasoning, then live deal links so you can buy it right now. No more tabs. No more deliberating.</p>
            </div>
        </div>
    </div>
    <div class="splash-divider"></div>
    """, unsafe_allow_html=True)

    if st.button("Start →"):
        st.session_state.phase = "intake_target"
        st.rerun()

# ── Phase: intake_target ──────────────────────────────────────────────────────
elif st.session_state.phase == "intake_target":
    render_phase_strip("intake_target")
    st.markdown('<span class="section-label">What are you buying?</span>', unsafe_allow_html=True)
    st.markdown('<p class="body-text">Name the thing you keep putting off. Be as specific or vague as you like — we\'ll narrow it down together.</p>', unsafe_allow_html=True)

    with st.form("intake_form", clear_on_submit=False):
        target = st.text_input(
            "Item",
            placeholder="e.g. an espresso machine I keep putting off buying",
            label_visibility="hidden",
        )
        submitted = st.form_submit_button("Begin →")

    if submitted and target:
        st.session_state.chat_history.append({"role": "USER", "message": f"I want to buy: {target}"})
        prompt = ("You are an efficient personal shopper. Look at the chat history and ask ONE "
                  "direct, targeted question to narrow down the user's preferences (e.g., budget, "
                  "dealbreakers, style). Do not offer options yet. Just ask the question.")
        with st.spinner("Thinking…"):
            question = ask_cohere(prompt)
            st.session_state.chat_history.append({"role": "CHATBOT", "message": question})
        st.session_state.phase = "intake_questions"
        st.rerun()

# ── Phase: intake_questions ───────────────────────────────────────────────────
elif st.session_state.phase == "intake_questions":
    render_phase_strip("intake_questions")
    st.markdown('<span class="section-label">A few quick questions</span>', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["message"].startswith("I want to buy:"):
            st.chat_message("user").write(msg["message"])
        elif msg["role"] == "USER":
            st.chat_message("user").write(msg["message"])
        else:
            st.chat_message("assistant").write(msg["message"])
    user_answer = st.chat_input("Your answer…")
    if user_answer:
        st.session_state.chat_history.append({"role": "USER", "message": user_answer})
        st.session_state.question_count += 1
        if st.session_state.question_count < MAX_QUESTIONS:
            prompt = ("You are an efficient personal shopper. Look at the chat history and ask ONE "
                      "direct, targeted follow-up question to narrow down preferences. No options yet.")
            with st.spinner("Thinking…"):
                question = ask_cohere(prompt)
                st.session_state.chat_history.append({"role": "CHATBOT", "message": question})
            st.rerun()
        else:
            st.session_state.phase = "curation"
            st.rerun()

# ── Phase: curation ───────────────────────────────────────────────────────────
elif st.session_state.phase == "curation":
    render_phase_strip("curation")
    st.markdown('<span class="section-label">Scanning the web</span>', unsafe_allow_html=True)
    st.markdown('<p class="body-text">Good. I have what I need. Searching now — this takes a moment.</p>', unsafe_allow_html=True)
    with st.spinner("Searching…"):
        query_prompt = ("Based on our chat history, write a highly specific Google search query "
                        "to find the best products for this user. Output ONLY the search query text.")
        search_query = ask_cohere(query_prompt, temp=0.3).strip(' "')
        tavily_results = tavily.search(query=search_query, search_depth="advanced", max_results=5)
        context = json.dumps(tavily_results.get("results", []))
        json_prompt = f"""You are a strict parser. Review this raw search data: {context}
Extract exactly 5 distinct products that fit the user's preferences from the chat history.
Return ONLY valid JSON in this exact format, with no markdown formatting or extra text:
[{{"id": 1, "name": "Product A", "price": "$100", "reason": "Why it fits", "pros": "Key strengths", "cons": "Main tradeoffs", "best_for": "Type of buyer"}}, ...]"""
        options_response = ask_cohere(json_prompt, temp=0.1)
        clean_json = options_response.replace("```json", "").replace("```", "").strip()
        try:
            st.session_state.products = json.loads(clean_json)
        except json.JSONDecodeError:
            st.error("Could not parse product data.")
            st.code(clean_json)
            st.stop()
        factor_prompt = f"""Look at these products: {json.dumps(st.session_state.products)}.
Identify exactly 4 key differentiating factors (e.g., Price, Durability, Weight, Aesthetics).
Return ONLY a comma-separated list of the 4 factors. No intro, no outro."""
        factors_raw = ask_cohere(factor_prompt, temp=0.1).strip()
        st.session_state.factors = factors_raw
        st.session_state.factors_list = [f.strip() for f in factors_raw.split(",") if f.strip()]
        st.session_state.ranked_factors = st.session_state.factors_list[:]
    st.session_state.phase = "ranking"
    st.rerun()

# ── Phase: ranking ────────────────────────────────────────────────────────────
elif st.session_state.phase == "ranking":
    render_phase_strip("ranking")
    st.markdown('<span class="section-label">Your priorities</span>', unsafe_allow_html=True)
    st.markdown('<p class="body-text">Five options found. Four factors separate them. Drag the blocks below to rank what matters most to you — top is most important.</p>', unsafe_allow_html=True)

    factors = st.session_state.factors_list

    # Ensure there's an initial ranked_factors list
    if "ranked_factors" not in st.session_state or not st.session_state.ranked_factors:
        st.session_state.ranked_factors = factors[:]

    # Render the custom HTML drag-and-drop widget which syncs to a hidden Streamlit input
    render_drag_rank(factors)

    # Bridge input — invisible, used only for JS→Streamlit sync
    st.markdown("""<style>
    div[data-testid="stTextInput"]:has(input[aria-label="ranked_factors_bridge"]) {
        position: absolute !important; opacity: 0 !important;
        pointer-events: none !important; height: 0 !important; overflow: hidden !important;
    }
    </style>""", unsafe_allow_html=True)
    bridge = st.text_input(
        "ranked_factors_bridge",
        value=", ".join(st.session_state.ranked_factors),
        label_visibility="hidden",
        key="ranked_factors_bridge",
    )

    # If the bridge was updated by JS, parse and update session state
    if bridge:
        parsed = [s.strip() for s in bridge.split(",") if s.strip()]
        if parsed and set(parsed) == set(factors) and parsed != st.session_state.ranked_factors:
            st.session_state.ranked_factors = parsed
    if st.button("Score Products →"):
        st.session_state.user_ranking = ", ".join(st.session_state.ranked_factors)
        st.session_state.phase = "scoring"
        st.rerun()

# ── Phase: scoring ────────────────────────────────────────────────────────────
elif st.session_state.phase == "scoring":
    render_phase_strip("scoring")
    st.markdown('<span class="section-label">Scoring…</span>', unsafe_allow_html=True)
    with st.spinner("Calculating…"):
        scoring_prompt = f"""Here is the original list of products: {json.dumps(st.session_state.products)}
The user ranked their priorities from most to least important: {st.session_state.user_ranking}.
Evaluate each product against these ranked priorities. Return the top 3 highest-scoring products.
For each product, also generate 3 concise stats that matter given the user's ranking (e.g., if Price was #1, include a price comparison stat).
Return ONLY valid JSON in this format:
[{{"id": 1, "name": "Product A", "price": "$100", "reason": "Scored highest because...",
   "pros": "Key strengths", "cons": "Main tradeoffs", "best_for": "Type of buyer",
   "stats": [{{"label": "Price tier", "value": "Mid-range"}}, {{"label": "Build quality", "value": "Excellent"}}, {{"label": "Ease of use", "value": "Beginner-friendly"}}]}}]"""
        scoring_response = ask_cohere(scoring_prompt, temp=0.1)
        clean_json = scoring_response.replace("```json", "").replace("```", "").strip()
        try:
            st.session_state.final_products = json.loads(clean_json)
        except json.JSONDecodeError:
            st.error("Could not parse scoring data.")
            st.code(clean_json)
            st.stop()
    st.session_state.phase = "choice"
    st.rerun()

# ── Phase: choice ─────────────────────────────────────────────────────────────
elif st.session_state.phase == "choice":
    render_phase_strip("choice")
    st.markdown('<span class="section-label">Your top three matches</span>', unsafe_allow_html=True)
    st.markdown('<p class="body-text">Here are your best options, scored against your priorities. Review the details, then choose one to find the best deals.</p>', unsafe_allow_html=True)

    rank_labels = ["First choice", "Runner-up", "Third option"]
    numerals = ["I", "II", "III"]

    for i, p in enumerate(st.session_state.final_products):
        stats = p.get("stats", [])
        stats_html = ""
        if stats:
            stats_items = "".join([
                f'<div class="stat-item"><span class="stat-label">{s["label"]}</span>'
                f'<span class="stat-value">{s["value"]}</span></div>'
                for s in stats
            ])
            stats_html = f'<div class="choice-stats">{stats_items}</div>'

        pros = p.get("pros", "")
        cons = p.get("cons", "")
        best_for = p.get("best_for", "")

        details_rows = ""
        if pros:
            details_rows += f'<div class="choice-detail-row"><span class="choice-detail-label">Strengths</span><span>{pros}</span></div>'
        if cons:
            details_rows += f'<div class="choice-detail-row"><span class="choice-detail-label">Tradeoffs</span><span>{cons}</span></div>'
        if best_for:
            details_rows += f'<div class="choice-detail-row"><span class="choice-detail-label">Best for</span><span>{best_for}</span></div>'

        details_html = f'<div class="choice-details">{details_rows}</div>' if details_rows else ""

        border_accent = "2px solid var(--ink)" if i == 0 else "2px solid var(--rule-light)"

        st.markdown(f"""
        <div class="choice-card" style="border-left:{border_accent};">
            <div class="choice-card-header">
                <div class="choice-card-meta">
                    <span class="choice-rank">{rank_labels[i]}</span>
                    <p class="choice-name">{p['name']}</p>
                </div>
                <span class="choice-price">{p['price']}</span>
            </div>
            <p class="choice-reason">{p['reason']}</p>
            {details_html}
            {stats_html}
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Find deals for this →", key=f"choose_{i}"):
            st.session_state.chosen_product = p
            st.session_state.phase = "deals"
            st.rerun()

# ── Phase: deals ──────────────────────────────────────────────────────────────
elif st.session_state.phase == "deals":
    render_phase_strip("deals")
    chosen = st.session_state.chosen_product

    if "deal_results" not in st.session_state:
        st.markdown('<span class="section-label">Hunting for deals…</span>', unsafe_allow_html=True)
        with st.spinner("Searching the web for the best prices…"):
            deal_query = f"{chosen['name']} best price discount buy online"
            st.session_state.deal_results = (
                tavily.search(query=deal_query, search_depth="basic").get("results", [])[:5]
            )
        st.rerun()

    st.markdown('<span class="section-label">Best deals found</span>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="info-band"><strong>Your choice</strong><p>{chosen["name"]} — {chosen["price"]}</p></div>',
        unsafe_allow_html=True,
    )

    for result in st.session_state.deal_results:
        st.markdown(f"""
        <div class="deal-row">
            <span class="deal-title">{result['title']}</span>
            <a class="deal-link" href="{result['url']}" target="_blank" rel="noopener">Open ↗</a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<p class="closing">The research is done. Stop deliberating and buy it.</p>', unsafe_allow_html=True)
    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to choices"):
            if "deal_results" in st.session_state:
                del st.session_state.deal_results
            st.session_state.phase = "choice"
            st.rerun()
    with col2:
        if st.button("Start over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()