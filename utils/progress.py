"""Parse GitHub-flavored task list Markdown into structured blocks, compute completion stats, and bridge widget state for Streamlit checkboxes."""

import hashlib
import re
from collections.abc import Iterable

TASK_RE = re.compile(r"^(\s*)[-*]\s*\[([ xX])\]\s*(.+?)\s*$")


def strip_task_syntax(markdown: str) -> str:
    """Convert GitHub-flavored ``- [ ]`` / ``- [x]`` task lines into plain ``- `` bullet lines.

    Args:
        markdown: Raw Markdown that may contain task-list items.

    Returns:
        Markdown with task syntax removed; non-task lines are passed through unchanged.
    """
    out = []
    for line in markdown.splitlines():
        m = TASK_RE.match(line)
        if m:
            indent = m.group(1)
            text = m.group(3)
            out.append(f"{indent}- {text}")
        else:
            out.append(line)
    return "\n".join(out)


def _make_id(section: str, text: str, idx: int) -> str:
    """Return a stable short hash id for a task item (derived from section + text + position).

    Args:
        section: Most-recent Markdown heading the task appears under.
        text: The task line's visible text.
        idx: 1-based ordinal of the task within the parse (used to disambiguate identical lines).

    Returns:
        A 10-character SHA-1 prefix used as a stable progress key across reruns.
    """
    h = hashlib.sha1(f"{section}::{text}::{idx}".encode()).hexdigest()
    return h[:10]


def parse_blocks(markdown: str) -> list[dict]:
    """Parse Markdown into an ordered list of blocks suitable for sequential rendering.

    Args:
        markdown: The Markdown source to parse.

    Returns:
        Ordered list where each block is either:

        - ``{"type": "md", "text": <raw markdown chunk>}`` — render verbatim with ``st.markdown``.
        - ``{"type": "task", "id": <hash>, "text": <task text>, "section": <heading>}`` —
          render as an interactive ``st.checkbox``.
    """
    blocks: list[dict] = []
    md_buffer: list[str] = []
    current_section = ""
    task_idx = 0

    def flush_md() -> None:
        if md_buffer:
            blocks.append({"type": "md", "text": "\n".join(md_buffer)})
            md_buffer.clear()

    for line in markdown.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            current_section = heading.group(2).strip()
            md_buffer.append(line)
            continue

        task = TASK_RE.match(line)
        if task:
            flush_md()
            text = task.group(3).strip()
            task_idx += 1
            blocks.append(
                {
                    "type": "task",
                    "id": _make_id(current_section, text, task_idx),
                    "text": text,
                    "section": current_section,
                }
            )
        else:
            md_buffer.append(line)
    flush_md()
    return blocks


def iter_tasks(blocks: Iterable[dict]) -> list[dict]:
    """Return only the task blocks from a parsed block list.

    Args:
        blocks: Output of :func:`parse_blocks`.

    Returns:
        A list containing only the ``type == "task"`` entries.
    """
    return [b for b in blocks if b.get("type") == "task"]


def completion_stats(blocks: Iterable[dict], progress: dict) -> tuple[int, int]:
    """Return ``(done, total)`` counts for the parsed blocks against the progress map.

    Args:
        blocks: Output of :func:`parse_blocks`.
        progress: Persisted ``{item_id: bool}`` map (typically loaded from the session JSON).

    Returns:
        Tuple of ``(checked_count, total_task_count)``.
    """
    tasks = iter_tasks(blocks)
    total = len(tasks)
    done = sum(1 for t in tasks if progress.get(t["id"]))
    return done, total


def compute_live_progress(
    sections: list[tuple[str, str]],
    base_progress: dict,
) -> tuple[int, int, dict]:
    """Seed Streamlit checkbox widget state from persisted progress and return the live (done, total, progress_dict) read back from widget state.

    The key trick: Streamlit checkbox widgets store their value in ``st.session_state[key]``.
    On a cold rerun (e.g. after a session resume) the widget keys may not yet exist, so we
    seed them from ``base_progress``. Once a key exists we trust the widget state — it
    already reflects the user's latest toggle for this rerun.

    Args:
        sections: List of ``(markdown_text, state_key_prefix)`` pairs — one per tracked
            section. ``state_key_prefix`` namespaces the widget key (e.g. ``"a2"`` for the
            Learning Path tab).
        base_progress: Persisted progress dict used to seed widget state for any newly
            encountered task IDs.

    Returns:
        Tuple ``(done, total, full_progress)``.

        ``full_progress`` contains only IDs for tasks present in the supplied sections
        (stale IDs from ``base_progress`` are intentionally dropped) so the sidebar and
        export stats stay accurate as the markdown evolves.
    """
    import streamlit as st  # local import keeps the module unit-testable without Streamlit

    full: dict = {}
    done = 0
    total = 0

    for markdown, state_key in sections:
        for block in parse_blocks(markdown):
            if block["type"] != "task":
                continue
            total += 1
            cb_key = f"{state_key}_{block['id']}"
            if cb_key not in st.session_state:
                st.session_state[cb_key] = bool(base_progress.get(block["id"], False))
            checked = bool(st.session_state[cb_key])
            full[block["id"]] = checked
            if checked:
                done += 1

    return done, total, full
