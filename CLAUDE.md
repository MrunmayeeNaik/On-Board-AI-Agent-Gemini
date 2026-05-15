# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Instructions
When creating a new function always include a one-sentence description of what it does
## Project

Multi-agent employee-onboarding assistant built on Gemini 2.0 Flash with a Streamlit UI. Three agents collaborate: **Provisioning Coordinator** (Agent 1) builds a tool-access checklist, Day-1 schedule, and key contacts from a profile; **Learning Path Generator** (Agent 2) reads the company handbook plus Agent 1's output to produce a 30-60-90 day plan; **HR Buddy** (Agent 3) is a multi-turn chat that answers HR questions grounded in the handbook.

## Common commands

PowerShell on Windows. Replace `Activate.ps1` with `activate` on bash/zsh.

```powershell
# one-time setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# create .env with: GEMINI_API_KEY=<your key>

# run the Streamlit app
streamlit run app.py

# smoke-test the Gemini client in isolation (current contents of app.py)
python app.py
```

There is no test suite, linter, or build step configured. Do not invent commands for these — add the tooling first if needed.

## Architecture

The system has three layers; respect the boundaries when adding code.

**`utils/` — pure I/O and LLM access.** No business logic.
- `gemini_client.py` is the *only* place that talks to Gemini (`call_gemini(prompt, context="")`). All agents must go through it so the model name (`gemini-2.0-flash`) and API key handling stay centralized.
- `doc_loader.py` loads structured data (`load_tools`, `load_org_chart`) and PDFs (`load_pdf`, `load_handbook`). Data files live under `data/` and are keyed by `department`.
- `prompt_templates.py` will hold one system prompt per agent — keep prompts here, not inline in agent modules, so they're easy to tune.

**`agents/` — one agent per file, pure functions.** Each agent takes inputs and returns a dict; no file I/O, no `st.session_state`. This keeps them testable and lets the orchestrator handle persistence.
- `agent1_provisioning.py` is **JSON-first, LLM-second**: it looks up tools/contacts/schedules deterministically via `doc_loader`, then asks Gemini only to write the narrative. This avoids hallucinated tools or fake email addresses — the most common failure mode of a pure-LLM provisioning agent. Preserve this pattern.
- `agent2_learning.py` injects the full handbook text as Gemini context. **No RAG / vector DB** — Gemini 2.0 Flash's 1M-token window fits typical handbooks. Don't add a vector store unless handbooks routinely exceed ~500 pages.
- `agent3_hrbuddy.py` is multi-turn; the orchestrator passes `history` in on each call. The system prompt instructs it to cite handbook sections and escalate to a named contact from Agent 1's output when out-of-scope.
- `orchestrator.py` is the only module that reads/writes session state. It runs Agent 1 → Agent 2 sequentially on intake, then routes chat turns to Agent 3.

**`ui/` — Streamlit tabs, one per agent.** `app.py` mounts three tabs: setup → learning plan → chat. Tabs 2 and 3 are gated until Tab 1 has produced a session. UI code talks to the orchestrator, never directly to agents or `utils`.

**`data/` — config + persistence.**
- `tools_list.json` and `org_chart.json` are department-keyed lookups for Agent 1.
- `data/sessions/<slug>.json` is the per-employee session record (`profile`, `agent1_output`, `agent2_output`, `chat_history`). Slug = `f"{name}_{role}".lower().replace(" ","_")`.
- `data/personas/` holds preset employee profiles for demos.

## Conventions

- The handbook source pattern is "upload-or-fallback": Streamlit upload takes precedence, otherwise `data/handbook_sample.pdf`. New handbook-consuming agents should accept already-extracted text, not a path — extraction belongs in `doc_loader`.
- Agents return `{ ..., "summary_md": "..." }` so the UI can render a single Markdown block without re-formatting per agent.
- `.env` holds `GEMINI_API_KEY`; loaded by `utils/gemini_client.py` via `python-dotenv`.
