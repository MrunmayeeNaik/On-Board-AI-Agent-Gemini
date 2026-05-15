import json
import os
import PyPDF2


def load_tools(department: str) -> list:
    """Return the tool-access checklist for a given department.

    Args:
        department: Department name (e.g., "Engineering", "Sales").

    Reads data/tools_list.json and returns the list mapped to `department`.
    Falls back to a generic tool list if the file or key is missing.
    """
    tools_path = os.path.join("data", "tools_list.json")
    try:
        with open(tools_path, "r") as f:
            tools_data = json.load(f)
        return tools_data.get(department, ["Slack", "Google Workspace", "Zoom"])
    except FileNotFoundError:
        return ["Slack", "Google Workspace", "Zoom"]


def load_org_chart(department: str) -> dict:
    """Return the org-chart slice (manager, peers, key contacts) for a department.

    Args:
        department: Department name to look up.

    Reads data/org_chart.json and returns the dict for `department`,
    or an empty dict if the file or key is missing.
    """
    org_path = os.path.join("data", "org_chart.json")
    try:
        with open(org_path, "r") as f:
            org_data = json.load(f)
        return org_data.get(department, {})
    except FileNotFoundError:
        return {}


def load_pdf(file_path: str) -> str:
    """Extract all text from a PDF stored on disk.

    Args:
        file_path: Absolute or relative path to a .pdf file.

    Returns the concatenated page text, or an error string if extraction fails.
    """
    try:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Could not load PDF: {str(e)}"


def load_handbook(uploaded_file=None, fallback_path: str = "data/handbook_sample.pdf") -> str:
    """Load company handbook text from a Streamlit upload, with a sample-PDF fallback.

    Args:
        uploaded_file: A Streamlit UploadedFile (file-like) or None.
        fallback_path: Path to the sample handbook used when no upload is provided.

    Returns the extracted handbook text. Used by Agent 2 (learning path) and
    Agent 3 (HR Buddy) as their domain context.
    """
    pass
