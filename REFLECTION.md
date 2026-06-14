# Project Reflection - Unstuck

---

## 1. How did your prompts evolve?

Three things made the biggest difference: giving the model a role (`"You are a strict parser"`) before the task, using a filled-in example instead of describing the format I wanted, and splitting search query generation and result parsing into two separate prompts instead of one. Each change came from watching the output break in a specific way and tracing it back to the prompt.

---

## 2. Most revealing failure mode?

The "Continue" button that silently did nothing. Users could select a product, click Continue, and the app just sat there. The cause was a JavaScript trick to pass data between the interactive card and Streamlit that works locally but gets blocked in deployment with no error message anywhere. The fix was to ditch the clever approach entirely and use a plain Streamlit button. Lesson: when a framework has strong opinions about how it works, go with them.

---

## 3. Main limitations?

Search quality is the hardest ceiling, as for niche products, results are thin and the model fills gaps with guesses. Price data is also unreliable since the model is reading it off web pages rather than a structured source. Given more time, I'd swap LLM price extraction for a dedicated pricing API.

---

## 4. What would you do differently?

Add a debug mode on day one. I had no visibility into what was happening between the user's input and the final output, like what search query the model wrote, what came back from Tavily, and where JSON was failing. That cost a lot of time. I'd also be more conservative with custom JavaScript from the start; the fancier the interaction, the harder it is to debug when something goes wrong in production.
