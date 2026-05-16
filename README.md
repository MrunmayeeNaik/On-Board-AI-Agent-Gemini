# On-Board AI Agent

A multi-agent employee-onboarding assistant built on **Gemini** with a polished **Streamlit** UI. Three specialised agents collaborate to take a new hire from "first day jitters" to "ready to contribute" — generating a personalised provisioning plan, a 30-60-90 day learning roadmap, and an always-available HR buddy grounded in your company handbook.

---

## Features

| | |
|---|---|
| 🛠️ **Provisioning Coordinator (Agent 1)** | JSON-first, LLM-second. Looks up tools, org chart, and Day-1 schedule from `data/` then asks Gemini to write the narrative. No hallucinated tools or fake email addresses. |
| 📚 **Learning Path Generator (Agent 2)** | Builds a 30-60-90 day plan grounded in the company handbook and Agent 1's output. Whole handbook is fed into Gemini's context window — no vector DB required. |
| 💬 **HR Buddy (Agent 3)** | Multi-turn chat answering HR questions, citing handbook sections, and escalating to a named contact (from Agent 1's output) when out of scope. |
| ✅ **Interactive progress tracker** | Learning Path renders task items as checkboxes. Progress is persisted to disk and reflected live in the sidebar, hero badges, and metric tiles. |
| 👤 **Persona presets** | One-click prefill from `data/personas/*.json` for instant demos. |
| 📂 **Saved-session browser** | Sidebar lists every previous onboarding session — click to resume. |
| 📄 **PDF export** | Download a styled, multi-page onboarding pack (profile + provisioning + learning plan + chat log) with a single click. |
| 🎨 **Polished UI** | Custom CSS: gradient hero banner, metric tiles, themed tabs/sidebar, animated progress bar. No third-party Streamlit components. |

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                          app.py                            │  Streamlit entry: mounts sidebar + tabs
└──────────┬─────────────────────────────────────┬───────────┘
           │                                     │
           ▼                                     ▼
   ┌──────────────┐                       ┌──────────────┐
   │     ui/      │                       │ orchestrator │      Only module touching disk for sessions
   │  (tabs, CSS, │                       │              │
   │   sidebar)   │                       └──────┬───────┘
   └──────────────┘                              │
                                                 ▼
                                ┌────────────────┴────────────────┐
                                ▼               ▼                 ▼
                        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                        │   agent1     │ │   agent2     │ │   agent3     │
                        │ Provisioning │ │  Learning    │ │  HR Buddy    │
                        └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                               │                │                │
                               └────────────────┴────────────────┘
                                                ▼
                                       ┌──────────────────┐
                                       │       utils      │  doc_loader · gemini_client
                                       │                  │  prompt_templates · progress · export
                                       └─────────┬────────┘
                                                 ▼
                                            ┌─────────┐
                                            │ Gemini  │
                                            └─────────┘
```

**Layers (and what they're allowed to do):**

- **`utils/`** — pure I/O and LLM access. No business logic. Every Gemini call routes through `gemini_client.call_gemini`.
- **`agents/`** — one agent per file, pure functions. No file I/O, no `st.session_state`. The `orchestrator` is the only module that reads/writes sessions on disk.
- **`ui/`** — Streamlit tabs and components. Talks to the orchestrator, never directly to agents or LLM.
- **`data/`** — config (`tools_list.json`, `org_chart.json`, `schedules.json`) + persistence (`sessions/`, `personas/`) + the bundled sample handbook.

---

## Project structure

```
.
├── app.py                          # Streamlit entrypoint
├── agents/
│   ├── orchestrator.py             # Session I/O + agent routing
│   ├── agent1_provisioning.py      # Provisioning Coordinator
│   ├── agent2_learning.py          # Learning Path Generator
│   └── agent3_hrbuddy.py           # HR Buddy
├── ui/
│   ├── styles.py                   # Custom CSS + hero / metric helpers
│   ├── sidebar.py                  # Persona + session browser + PDF export
│   ├── tab1_setup.py               # Setup form + handbook upload
│   ├── tab2_learning.py            # Interactive learning path
│   └── tab3_chat.py                # HR chat with suggested questions
├── utils/
│   ├── gemini_client.py            # Centralised Gemini access
│   ├── doc_loader.py               # JSON + PDF loaders
│   ├── prompt_templates.py         # One system prompt per agent
│   ├── progress.py                 # Markdown task parsing + widget bridging
│   └── export.py                   # Markdown + PDF export builders
├── data/
│   ├── tools_list.json             # Department → tools mapping
│   ├── org_chart.json              # Department → head, email, team size
│   ├── schedules.json              # Department → Day-1 schedule
│   ├── company_handbook.pdf        # Bundled sample handbook
│   ├── personas/                   # Persona presets (JSON)
│   └── sessions/                   # Persisted per-employee sessions (JSON)
├── .streamlit/config.toml          # Streamlit theme overrides
├── requirements.txt
├── CLAUDE.md                       # Project conventions
└── README.md
```

---

## Setup

**Prerequisites:** Python 3.10+ and a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate              # macOS / Linux
# .\.venv\Scripts\Activate.ps1         # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env
```

---

## Developer setup

```bash
pip install -e ".[dev]"          # installs ruff + pre-commit alongside runtime deps
pre-commit install               # wires up the git pre-commit hook
pre-commit run --all-files       # one-time check across the whole repo
```

The hook runs `ruff check --fix`, `ruff format`, `gitleaks` (secret scan), and a handful of
hygiene checks (trailing whitespace, EOF newlines, large file guard, merge conflict markers).
Configuration lives in `pyproject.toml` (ruff), `.gitleaks.toml` (secret scan), and
`.pre-commit-config.yaml` (hook orchestration).

---

## Running

```bash
streamlit run app.py
```

The app opens at <http://localhost:8501>.

1. **Setup tab** — fill in the new hire's name, role, department. Optionally upload a custom handbook PDF. Click **Generate Onboarding Plan**.
2. **Learning Path tab** — review the 30-60-90 day plan and check items off as they're completed. Progress is saved automatically.
3. **HR Buddy tab** — ask anything about company policy. Replies cite handbook sections; out-of-scope questions are escalated to a named contact from Agent 1's output.
4. **Sidebar** — load a persona for instant prefill, resume any previous session, or download the full onboarding pack as PDF.

---

## Customising for your company

| What | Where | How |
|---|---|---|
| Tools per department | `data/tools_list.json` | Edit the JSON object; keys are department names. |
| Org chart (head, email, team size) | `data/org_chart.json` | Edit the JSON object. Agent 1 will use the values verbatim. |
| Day-1 schedules | `data/schedules.json` | Edit the per-department time → activity maps. |
| Company handbook | Upload in the Setup tab, **or** replace `data/company_handbook.pdf` | The Setup-tab upload takes precedence per session. |
| Persona presets | `data/personas/*.json` | One file per persona, with `name`, `role`, `department`. |
| Agent prompts / tone | `utils/prompt_templates.py` | Each agent has its own builder function — tune freely. |
| Suggested HR questions | `ui/tab3_chat.py` (`SUGGESTED_QUESTIONS`) | Edit the list. |
| Visual theme | `ui/styles.py` and `.streamlit/config.toml` | CSS variables at the top of `CUSTOM_CSS` set the accent gradient. |

---

## How progress tracking works

Agent 1 and Agent 2 are instructed (via their prompts) to format every actionable item as a GitHub-flavored task list line:

```markdown
- [ ] Set up local dev environment
- [x] Pair with a senior engineer
```

At render time, `utils.progress.parse_blocks` walks the Markdown line-by-line, extracting `(section, text, position)` triples for each task and hashing them into stable 10-character IDs. The Learning Path tab renders these as `st.checkbox` widgets; `app.py` reads back the live widget state at the top of each rerun via `compute_live_progress` and writes the resulting `{id: bool}` map onto `session["progress"]`. The sidebar, hero badges, and metric tiles all read this dict — so changes propagate instantly to every part of the UI.

---

## Sessions & persistence

- **Where:** `data/sessions/<name>_<role>.json` — slug is lowercased with spaces replaced by underscores.
- **What's stored:** `profile`, `agent1_output`, `agent2_output`, `chat_history`, `progress`, and `handbook` (filename + extracted text).
- **When it's written:** at the end of intake; on every chat turn (`run_chat`); whenever the user toggles a Learning Path checkbox (`save_progress`).
- **Resuming:** the sidebar lists existing sessions sorted by most-recently-modified — one click restores everything including chat history.

---

## Conventions

- Every new function gets a one-sentence summary docstring (per `CLAUDE.md`). Public functions also document `Args:` and `Returns:` in Google style.
- The handbook source pattern is "upload-or-fallback": Streamlit upload takes precedence, otherwise the bundled `data/company_handbook.pdf`.
- Agents return Markdown strings under `summary_md` so the UI can render them in one shot.
- `.env` holds `GEMINI_API_KEY`; loaded by `utils/gemini_client.py` via `python-dotenv`.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| LLM | Gemini 2.0 Flash | 1M-token context fits typical handbooks without RAG. Fast, cheap. |
| UI | Streamlit + custom CSS | Single-file deployment, instant prototyping. No JS toolchain. |
| PDF export | `fpdf2` | Pure-Python, zero system dependencies, small footprint. |
| PDF reading | `PyPDF2` | Lightweight, ships with reliable text extraction for most handbooks. |
| Config | `python-dotenv` | Standard, well-understood. |

---

## License

Internal project — no license declared. Add one before publishing.
