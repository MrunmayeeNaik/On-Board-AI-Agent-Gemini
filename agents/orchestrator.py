import json
import os

from agents.agent1_provisioning import run_agent1
from agents.agent2_learning import run_agent2
from agents.agent3_hrbuddy import run_agent3


def _make_slug(name: str, role: str) -> str:
    """Return a filesystem-safe session identifier from employee name and role."""
    return f"{name}_{role}".lower().replace(" ", "_")


def _session_path(slug: str) -> str:
    """Return the path to the JSON file for a given session slug."""
    return os.path.join("data", "sessions", f"{slug}.json")


def _load_session(slug: str) -> dict | None:
    """Load a session from disk, returning None if it does not exist."""
    path = _session_path(slug)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def _save_session(slug: str, session: dict) -> None:
    """Persist a session dict to disk, creating the sessions directory if needed."""
    os.makedirs(os.path.join("data", "sessions"), exist_ok=True)
    with open(_session_path(slug), "w") as f:
        json.dump(session, f, indent=2)


def run_intake(name: str, role: str, department: str) -> dict:
    """Run Agent 1 then Agent 2 sequentially, persist the session, and return it."""
    slug = _make_slug(name, role)

    agent1_raw = run_agent1(name=name, role=role, department=department)
    agent2_raw = run_agent2(
        name=name, role=role, department=department, agent1_output=agent1_raw
    )

    session = {
        "profile": {"name": name, "role": role, "department": department},
        "agent1_output": {"summary_md": agent1_raw},
        "agent2_output": {"summary_md": agent2_raw},
        "chat_history": [],
    }
    _save_session(slug, session)
    return session


def run_chat(name: str, role: str, question: str) -> dict:
    """Route a chat turn to Agent 3, append the exchange to history, persist, and return the response."""
    slug = _make_slug(name, role)
    session = _load_session(slug)
    if session is None:
        raise ValueError(f"No session found for '{slug}'. Run intake first.")

    history: list[dict] = session.get("chat_history", [])

    history_text = "\n".join(
        f"{turn['role'].upper()}: {turn['content']}" for turn in history
    )

    answer_raw = run_agent3(question=question, chat_history=history_text)

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer_raw})
    session["chat_history"] = history
    _save_session(slug, session)

    return {"summary_md": answer_raw, "chat_history": history}


def load_session(name: str, role: str) -> dict | None:
    """Load an existing session by name and role, returning None if not found."""
    return _load_session(_make_slug(name, role))
