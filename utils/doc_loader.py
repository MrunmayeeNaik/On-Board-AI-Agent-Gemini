"""Pure I/O helpers for loading structured department data (JSON) and handbook documents (PDF)."""

import json
import os

import PyPDF2


def load_tools(department: str) -> list[str]:
    """Return the tool-access checklist for a given department.

    Args:
        department: Department name as it appears in ``data/tools_list.json``
            (e.g. ``"Engineering"``, ``"Sales"``).

    Returns:
        List of tool names provisioned for the department. Falls back to a generic
        ``["Slack", "Google Workspace", "Zoom"]`` list when the file or key is missing.
    """
    tools_path = os.path.join("data", "tools_list.json")
    try:
        with open(tools_path) as f:
            tools_data = json.load(f)
        return tools_data.get(department, ["Slack", "Google Workspace", "Zoom"])
    except FileNotFoundError:
        return ["Slack", "Google Workspace", "Zoom"]


def load_org_chart(department: str) -> dict:
    """Return the org-chart slice (head, email, team size) for a department.

    Args:
        department: Department name as it appears in ``data/org_chart.json``.

    Returns:
        Dict with keys like ``head``, ``email``, ``team_size`` for the department.
        Empty dict if the file or key is missing.
    """
    org_path = os.path.join("data", "org_chart.json")
    try:
        with open(org_path) as f:
            org_data = json.load(f)
        return org_data.get(department, {})
    except FileNotFoundError:
        return {}


def load_pdf(file_path: str) -> str:
    """Extract all text from a PDF stored on disk.

    Args:
        file_path: Absolute or relative path to a ``.pdf`` file.

    Returns:
        Concatenated page text with newlines between pages, or a human-readable
        error string starting with ``"Could not load PDF:"`` if extraction fails.
    """
    try:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    except Exception as e:
        return f"Could not load PDF: {str(e)}"


def load_handbook(uploaded_file=None, fallback_path: str = "data/company_handbook.pdf") -> str:
    """Load company handbook text from a Streamlit upload, falling back to the on-disk sample PDF when no upload is provided.

    Args:
        uploaded_file: A Streamlit ``UploadedFile`` (file-like object) or ``None``.
        fallback_path: Path to the bundled sample PDF used when ``uploaded_file`` is ``None``.

    Returns:
        Extracted handbook text (UTF-8 string). Empty string if neither source exists.
        Used by Agent 2 (Learning Path) and Agent 3 (HR Buddy) as their domain context.
    """
    if uploaded_file is not None:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text
        except Exception as e:
            return f"Could not parse uploaded handbook: {str(e)}"

    if os.path.exists(fallback_path):
        return load_pdf(fallback_path)
    return ""
