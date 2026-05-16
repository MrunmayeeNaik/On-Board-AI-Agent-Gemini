"""The only module that touches disk for per-employee sessions. Runs Agent 1 → Agent 2 on intake and routes chat turns to Agent 3."""

import json
import os

from agents.agent1_provisioning import run_agent1
from agents.agent2_learning import run_agent2
from agents.agent3_hrbuddy import run_agent3

SESSIONS_DIR = os.path.join("data", "sessions")


def _make_slug(name: str, role: str) -> str:
    """Return a filesystem-safe session identifier derived from employee name and role.

    Args:
        name: Employee's full name (case-insensitive).
        role: Job title (case-insensitive).

    Returns:
        A lowercased, underscore-separated slug used as the session file's basename.
    """
    return f"{name}_{role}".lower().replace(" ", "_")


def _session_path(slug: str) -> str:
    """Return the absolute-on-cwd path to the JSON file for a given session slug.

    Args:
        slug: Output of :func:`_make_slug`.

    Returns:
        Path like ``data/sessions/<slug>.json``.
    """
    return os.path.join(SESSIONS_DIR, f"{slug}.json")


def _load_session(slug: str) -> dict | None:
    """Load a session from disk.

    Args:
        slug: Output of :func:`_make_slug`.

    Returns:
        The parsed session dict, or ``None`` if no file exists for that slug.
    """
    path = _session_path(slug)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _save_session(slug: str, session: dict) -> None:
    """Persist a session dict to disk, creating the sessions directory if needed.

    Args:
        slug: Output of :func:`_make_slug`.
        session: The session dict to write (pretty-printed with two-space indent).
    """
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    with open(_session_path(slug), "w") as f:
        json.dump(session, f, indent=2)


def run_intake(
    name: str,
    role: str,
    department: str,
    handbook_text: str = "",
    handbook_filename: str = "",
) -> dict:
    """Run Agent 1 then Agent 2 sequentially, persist the resulting session, and return it.

    Args:
        name: Employee's full name.
        role: Job title.
        department: Department name (drives Agent 1's deterministic lookups).
        handbook_text: Optional extracted handbook content (forwarded to Agent 2 and
            stored on the session so Agent 3 can use it for grounding later).
        handbook_filename: Display name of the uploaded handbook (used by the export).

    Returns:
        The full session dict containing ``profile``, ``agent1_output``, ``agent2_output``,
        ``chat_history`` (empty), ``progress`` (empty), and ``handbook``.
    """
    slug = _make_slug(name, role)

    agent1_raw = run_agent1(name=name, role=role, department=department)
    agent2_raw = run_agent2(
        name=name,
        role=role,
        department=department,
        agent1_output=agent1_raw,
        handbook_text=handbook_text,
    )

    session = {
        "profile": {"name": name, "role": role, "department": department},
        "agent1_output": {"summary_md": agent1_raw},
        "agent2_output": {"summary_md": agent2_raw},
        "chat_history": [],
        "progress": {},
        "handbook": {
            "filename": handbook_filename,
            "text": handbook_text,
            "uploaded": bool(handbook_text.strip()),
        },
    }
    _save_session(slug, session)
    return session


def run_chat(
    name: str,
    role: str,
    question: str,
    handbook_text: str = "",
    contacts_text: str = "",
) -> dict:
    """Route a chat turn to Agent 3 (with handbook + escalation contacts), append the exchange to history, persist, and return the response.

    Args:
        name: Employee's name — identifies the session.
        role: Job title — also part of the session slug.
        question: The user's current question to forward to Agent 3.
        handbook_text: Handbook content for grounding. Falls back to the value stored on
            the session if this argument is empty.
        contacts_text: ``Key Contacts`` excerpt from Agent 1's output, used for escalation
            suggestions.

    Returns:
        Dict with ``summary_md`` (the assistant's answer) and ``chat_history`` (the full
        running list of turns after appending this exchange).

    Raises:
        ValueError: If no saved session exists for the (name, role) pair.
    """
    slug = _make_slug(name, role)
    session = _load_session(slug)
    if session is None:
        raise ValueError(f"No session found for '{slug}'. Run intake first.")

    history: list[dict] = session.get("chat_history", [])

    history_text = "\n".join(f"{turn['role'].upper()}: {turn['content']}" for turn in history)

    answer_raw = run_agent3(
        question=question,
        chat_history=history_text,
        handbook_text=handbook_text or session.get("handbook", {}).get("text", ""),
        contacts_text=contacts_text,
    )

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer_raw})
    session["chat_history"] = history
    _save_session(slug, session)

    return {"summary_md": answer_raw, "chat_history": history}


def load_session(name: str, role: str) -> dict | None:
    """Load an existing session by name and role.

    Args:
        name: Employee's name.
        role: Job title.

    Returns:
        The session dict, or ``None`` if no matching session is on disk.
    """
    return _load_session(_make_slug(name, role))


def list_sessions() -> list[dict]:
    """Return saved-session metadata sorted by most-recently modified.

    Returns:
        List of ``{"slug", "name", "role", "department"}`` dicts, one per JSON file in
        ``data/sessions/``. Files that fail to parse are silently skipped.
    """
    if not os.path.isdir(SESSIONS_DIR):
        return []
    rows: list[tuple[float, dict]] = []
    for fname in os.listdir(SESSIONS_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(SESSIONS_DIR, fname)
        try:
            with open(path) as f:
                data = json.load(f)
            profile = data.get("profile", {})
            rows.append(
                (
                    os.path.getmtime(path),
                    {
                        "slug": fname[:-5],
                        "name": profile.get("name", "Unknown"),
                        "role": profile.get("role", ""),
                        "department": profile.get("department", ""),
                    },
                )
            )
        except Exception:
            continue
    rows.sort(key=lambda r: r[0], reverse=True)
    return [r[1] for r in rows]


def save_progress(name: str, role: str, progress: dict) -> None:
    """Persist the per-item progress dict onto the saved session JSON.

    Args:
        name: Employee's name.
        role: Job title.
        progress: ``{task_id: bool}`` map representing which Learning Path items are
            checked. Overwrites any existing ``progress`` field.

    No-op if no session exists for the (name, role) pair.
    """
    slug = _make_slug(name, role)
    session = _load_session(slug)
    if session is None:
        return
    session["progress"] = progress
    _save_session(slug, session)
