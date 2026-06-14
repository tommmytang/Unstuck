# Unstuck — AI-Powered Purchase Decision Assistant

> *You've been thinking about buying it for weeks. Unstuck ends that in five minutes.*

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [How It Works](#how-it-works)
3. [Key Adaptations & Improvements](#key-adaptations--improvements)
4. [Prompt Engineering: Iteration & Examples](#prompt-engineering-iteration--examples)
5. [Evaluation](#evaluation)
6. [Recreating This Approach](#recreating-this-approach)
7. [Setup & Installation](#setup--installation)

---

## Project Overview

### The Problem

Decision fatigue is real. Most people spend hours — sometimes weeks — on purchase research: opening dozens of tabs, reading conflicting reviews, comparing specs they don't fully understand, and ultimately buying nothing (or panic-buying the wrong thing). Existing comparison tools surface information without helping the user *decide*.

### Intended User

Anyone staring at a purchase they keep putting off. The app is deliberately genre-agnostic: it works for a $40 book recommendation, a $400 espresso machine, or a $4,000 laptop. The user doesn't need to know what they're looking for — just *that* they're looking for something.

### Key Features

- **Natural-language intake** — users describe the purchase in plain English; no dropdowns, no category menus
- **AI-generated preference chips** — Cohere generates contextually relevant preference options for each product type (not generic filters)
- **Live web search** — Tavily fetches real-time product listings, reviews, and comparisons at search time, not from a stale database
- **LLM-driven product curation** — the model parses web results into 5 clean, structured product candidates
- **Drag-to-rank prioritisation** — users reorder four differentiating factors by importance before scoring
- **Preference-weighted scoring** — the model re-ranks candidates against the user's stated priorities
- **Live deal links** — Tavily searches for the best current prices on the chosen product, cached for one hour to avoid redundant API calls

---

## How It Works

Unstuck runs as a Streamlit app with a linear phase-based state machine. Each phase is a discrete UI + logic step; `st.session_state` carries all data between phases.

```
splash → intake_target → intake_options → curation → ranking → scoring → choice → deals
```

```python
# Phase transitions are driven by a single key in session state
_phase_order = ["splash", "intake_target", "intake_options",
                "curation", "ranking", "scoring", "choice", "deals"]

if st.session_state.phase == "curation":
    # ... do LLM work, then:
    st.session_state.phase = "ranking"
    st.rerun()
```

Each phase renders its own UI and either awaits user input (a button click or form submit) or does async LLM/search work before auto-advancing. The `ask_cohere()` helper passes the full conversation history on every call, giving the model context continuity across phases:

```python
def ask_cohere(prompt, temp=0.3):
    response = co.chat(
        message=prompt,
        chat_history=st.session_state.chat_history,  # full history every time
        model=MODEL_NAME,
        temperature=temp
    )
    return response.text
```

Deal results are cached with `@st.cache_data` to avoid re-querying Tavily if the user navigates back and forth:

```python
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_deals(product_name):
    deal_query = f"{product_name} best price discount buy online"
    return tavily.search(query=deal_query, search_depth="basic").get("results", [])[:5]
```

---

## Key Adaptations & Improvements

The starter app provided a basic Streamlit chat interface with a single Cohere call. The following changes were made to build a full decision-support flow.

### 1. Phase-based state machine (replacing a single chat loop)

The starter used an open-ended chat loop where the model could ask unlimited clarifying questions. This felt formless and often diverged. Replacing it with a strict phase machine gives the user clear progress and guarantees termination.

```python
# Before: open-ended chat
if prompt := st.chat_input("What are you looking for?"):
    response = ask_cohere(prompt)
    st.chat_message("assistant").write(response)

# After: phase-gated linear flow
if st.session_state.phase == "intake_target":
    with st.form("intake_form"):
        target = st.text_input("Item", placeholder="e.g. an espresso machine…")
        submitted = st.form_submit_button("Begin →")
    if submitted and target:
        st.session_state.intake_target = target
        st.session_state.phase = "intake_options"
        st.rerun()
```

### 2. Two-stage search: query generation → web fetch → structured parse

The starter passed user input directly to the model with no external grounding, producing hallucinated product names. The rewrite uses a two-stage RAG approach: first ask the model to generate a precise search query from the conversation context, then pass the raw web results back to the model for structured extraction.

```python
# Stage 1: model generates the search query
query_prompt = (
    "Based on our chat history, write a highly specific Google search query "
    "to find the best products for this user. Output ONLY the search query text."
)
search_query = ask_cohere(query_prompt, temp=0.3).strip(' "')

# Stage 2: fetch real web data
tavily_results = tavily.search(query=search_query, search_depth="advanced", max_results=5)
context = json.dumps(tavily_results.get("results", []))

# Stage 3: model parses web results into structured product data
json_prompt = f"""You are a strict parser. Review this raw search data: {context}
Extract exactly 5 distinct products that fit the user's preferences from the chat history.
Return ONLY valid JSON in this exact format, with no markdown formatting or extra text:
[{{"id": 1, "name": "Product A", "price": "$100", "reason": "Why it fits",
  "pros": "Key strengths", "cons": "Main tradeoffs", "best_for": "Type of buyer"}}, ...]"""
options_response = ask_cohere(json_prompt, temp=0.1)
```

### 3. Dynamic preference chip generation

Rather than showing fixed filter options, the app asks the model to generate preference options specific to each product category. A user buying a monitor gets different chips than a user buying a coffee grinder.

```python
prompt = (
    f"The user wants to buy: {target}. "
    "Generate exactly 8 short, distinct preference options a buyer of this product might care about. "
    "Examples for a laptop: Good battery life, Lightweight & portable, Fast performance, "
    "Great display, Budget-friendly, Gaming capable, Business/professional, Long-lasting build quality. "
    "Return ONLY a JSON array of 8 strings, no markdown, no intro. Just the array."
)
```

### 4. Preference-weighted scoring pass

The starter returned a flat list. After users rank four differentiating factors by drag-and-drop priority, a second LLM pass re-evaluates the candidate products against that ranked order, surfacing contextual stats tied to what the user cares most about.

```python
scoring_prompt = f"""Here is the original list of products: {json.dumps(st.session_state.products)}
The user ranked their priorities from most to least important: {st.session_state.user_ranking}.
Evaluate each product against these ranked priorities. Return the top 3 highest-scoring products.
For each product, also generate 3 concise stats that matter given the user's ranking
(e.g., if Price was #1, include a price comparison stat).
Return ONLY valid JSON in this format: [...]"""
```

### 5. JS iframe bridge bug fix (the "Continue does nothing" bug)

The original choice phase used a hidden `<input>` as a message bridge between a `st.components.v1.html` iframe and Streamlit's Python runtime. This relied on `window.parent.document.querySelector()` — which modern Streamlit sandboxes block with a same-origin policy, causing clicks to silently fail.

```javascript
// Before: broken cross-frame DOM write (silently fails in sandboxed iframes)
var stInput = window.parent.document.querySelector('input[aria-label="choice_bridge"]');
if (stInput) {
    stInput.value = selected.toString();
    stInput.dispatchEvent(new Event('input', { bubbles: true }));
}
```

```python
# After: native st.button() widgets rendered below the display iframe.
# These always trigger a Streamlit rerun — no iframe boundary to cross.
cols = st.columns(3)
for i, (col, p) in enumerate(zip(cols, products)):
    with col:
        if st.button(f"Choose: {p['name']}", key=f"choose_{i}", use_container_width=True):
            st.session_state.chosen_product = products[i]
            st.session_state.phase = "deals"
            st.rerun()
```

### 6. Custom typography and editorial UI

Streamlit's default UI was replaced entirely via injected CSS, using three imported typefaces (Cormorant Garamond for display headings, DM Sans for body, Martian Mono for labels and metadata). All Streamlit chrome is hidden; the design deliberately evokes a print editorial aesthetic to reduce cognitive load and project calm deliberateness — the opposite of the anxiety-inducing tab-soup the user is escaping.

---

## Prompt Engineering: Iteration & Examples

### Prompt 1 — Preference chip generation

**Goal:** Get 8 short, product-relevant preference labels as a JSON array.

**v1 (too open-ended):**
```
What are the most important features for someone buying {target}?
```
*Problem:* The model returned a paragraph of prose, sometimes with numbered lists, sometimes as a table. Parsing was fragile.

**v2 (format-specified but examples missing):**
```
List 8 preference options for buying {target}. Return as a JSON array of strings.
```
*Problem:* The model often returned generic options regardless of the product (e.g., "Good value for money", "High quality" for every category). Also occasionally added markdown fences despite the instruction.

**v3 (final — role-implicit, with worked example and strict output rule):**
```python
prompt = (
    f"The user wants to buy: {target}. "
    "Generate exactly 8 short, distinct preference options a buyer of this product might care about. "
    "Examples for a laptop: Good battery life, Lightweight & portable, Fast performance, "
    "Great display, Budget-friendly, Gaming capable, Business/professional, Long-lasting build quality. "
    "Return ONLY a JSON array of 8 strings, no markdown, no intro. Just the array."
)
```
*Why it works:* The concrete laptop example teaches format and specificity simultaneously. "ONLY" and "Just the array" redundantly enforce the output contract, which matters because Cohere sometimes prepends conversational filler.

---

### Prompt 2 — Web results → structured product list

**Goal:** Parse raw Tavily JSON into 5 clean product objects.

**v1:**
```
Here are some search results: {context}. 
List 5 good products the user might want.
```
*Problem:* Model returned bullet points with inconsistent fields. Price was sometimes omitted, sometimes a range, sometimes a sentence. JSON parsing failed ~40% of the time.

**v2 (JSON schema specified, but role was missing):**
```
Extract 5 products from this data: {context}.
Return JSON: [{"name": ..., "price": ..., "reason": ...}]
```
*Problem:* Still saw markdown fences, occasional 4 or 6 results, and the model occasionally fabricated products not present in the search data.

**v3 (final — role + strict parser persona + exact schema + zero-temperature):**
```python
json_prompt = f"""You are a strict parser. Review this raw search data: {context}
Extract exactly 5 distinct products that fit the user's preferences from the chat history.
Return ONLY valid JSON in this exact format, with no markdown formatting or extra text:
[{{"id": 1, "name": "Product A", "price": "$100", "reason": "Why it fits",
  "pros": "Key strengths", "cons": "Main tradeoffs", "best_for": "Type of buyer"}}, ...]"""
options_response = ask_cohere(json_prompt, temp=0.1)
```
*Why it works:* "You are a strict parser" primes the model into a deterministic extraction mode. `temp=0.1` minimises creativity drift. The inline JSON template with literal placeholder values (`"Product A"`, `"$100"`) is much harder to misinterpret than a description of the schema.

---

### Prompt 3 — Factor extraction

**Goal:** Identify 4 differentiating factors across the 5 product candidates.

**v1:**
```
What are the key differences between these products: {products}?
```
*Problem:* Returned a paragraph comparing the products rather than extractable factor labels.

**v2 (final):**
```python
factor_prompt = f"""Look at these products: {json.dumps(st.session_state.products)}.
Identify exactly 4 key differentiating factors (e.g., Price, Durability, Weight, Aesthetics).
Return ONLY a comma-separated list of the 4 factors. No intro, no outro."""
```
*Why it works:* The example values (`Price, Durability, Weight, Aesthetics`) teach the expected grain of abstraction — not too specific ("Gorilla Glass version"), not too vague ("Quality"). Comma-separated is the most robustly parseable plain-text format; it avoids the JSON-fence problem entirely.

---

## Evaluation

### How well does the app address its purpose?

The core goal is: take a vague, deferred purchase intention and produce a specific, actionable, personalised recommendation in under five minutes.

**Strengths:**
- The two-stage RAG approach grounds outputs in real product data and current pricing, eliminating the hallucination problem that makes LLM-only product recommendation unreliable
- The ranking step meaningfully changes results — the same five candidates score differently depending on whether the user puts price or build quality first
- The deal-finding step closes the loop: the user can act immediately

**Limitations:**
- Tavily results vary in quality by product category; niche or new products may surface thin or off-topic results
- The model's price parsing is imperfect — it may quote MSRP when a sale price appears elsewhere in the page
- The drag-rank bridge uses a `window.parent.document` DOM hack that works in local Streamlit but can silently break on sandboxed deployments (this is why native `st.button()` was used as the safe fallback for the choice phase)

---

### Example: Espresso Machine

**Input:** `"an espresso machine I keep putting off buying"`

**Preferences selected:** `Budget-friendly`, `Easy to use`, `Good build quality`

**User ranking (drag order):**
1. Price
2. Ease of Use
3. Build Quality
4. Features

**Top 3 output:**

| Rank | Product | Price | Key Stat |
|------|---------|-------|----------|
| 1st | Breville Bambino Plus | ~$500 | Best price-to-quality ratio in class |
| 2nd | De'Longhi Stilosa | ~$150 | Entry-level price, minimal learning curve |
| 3rd | Gaggia Classic Pro | ~$450 | Exceptional build; steeper learning curve noted |

**Deal links surfaced:** Amazon, Williams Sonoma, and Best Buy listings for the Breville Bambino Plus at current price.

---

### Example: Mechanical Keyboard

**Input:** `"a mechanical keyboard"`

**Preferences selected:** `Tactile feel`, `Quiet switches`, `Compact layout`

**User ranking:**
1. Switch feel
2. Noise level
3. Size
4. Price

**Top 3 output:**

| Rank | Product | Price | Key Stat |
|------|---------|-------|----------|
| 1st | Keychron Q2 (Gateron Pro Brown) | ~$180 | Best tactile-quiet balance; compact 65% layout |
| 2nd | Logitech MX Keys Mini | ~$100 | Near-silent; no per-key actuation feedback |
| 3rd | NuPhy Air75 | ~$110 | Wireless; low-profile tactile switches |

---

## Recreating This Approach

The core pattern here — **intake → grounded search → LLM parse → user ranking → re-score** — is transferable to any domain where a user needs to be guided from a vague goal to a specific choice.

**The key design decisions to preserve:**

**1. Use LLM-generated search queries, not raw user input.**
User input is often too vague to be a good search query. Have the model generate the query from the conversation context.

**2. Parse web results at near-zero temperature.**
When the job is extraction rather than generation, `temp=0.1` dramatically improves JSON reliability. Reserve higher temperatures for creative or generative tasks (chip generation, reason writing).

**3. Include a concrete output example in the prompt.**
For any prompt that must return structured data, show one complete example of the target format inline. A description of the schema is much weaker than a filled-in example.

**4. Use native Streamlit widgets for any action that must trigger a rerun.**
`st.components.v1.html` iframes are sandboxed on modern Streamlit deployments. Any JS→Python communication that relies on `window.parent.document` will silently fail. For user actions that must advance state, always reach for `st.button()`, `st.form()`, or a proper bidirectional component built with `declare_component`.

**5. Cache expensive search calls.**
```python
@st.cache_data(ttl=3600)
def fetch_deals(product_name):
    ...
```
A user navigating back-and-forth should not re-trigger API calls. `st.cache_data` with a TTL handles this cleanly.

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- A [Cohere API key](https://dashboard.cohere.com/)
- A [Tavily API key](https://tavily.com/)

### Install

```bash
git clone https://github.com/your-username/unstuck.git
cd unstuck
pip install streamlit cohere tavily-python
```

### Configure

Set environment variables (or edit the defaults at the top of `app.py` for local testing):

```bash
export COHERE_API_KEY="your-key-here"
export TAVILY_API_KEY="your-key-here"
```

### Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### Deploy to Streamlit Cloud

1. Push the repo to GitHub
2. Connect it at [share.streamlit.io](https://share.streamlit.io)
3. Add `COHERE_API_KEY` and `TAVILY_API_KEY` under **Settings → Secrets**

---

*Built with [Cohere](https://cohere.com) · [Tavily](https://tavily.com) · [Streamlit](https://streamlit.io)*
