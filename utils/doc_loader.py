import json
import os
import PyPDF2

def load_tools(department: str) -> list:
    tools_path = os.path.join("data", "tools_list.json")
    try:
        with open(tools_path, "r") as f:
            tools_data = json.load(f)
        return tools_data.get(department, ["Slack", "Google Workspace", "Zoom"])
    except FileNotFoundError:
        return ["Slack", "Google Workspace", "Zoom"]

def load_org_chart(department: str) -> dict:
    org_path = os.path.join("data", "org_chart.json")
    try:
        with open(org_path, "r") as f:
            org_data = json.load(f)
        return org_data.get(department, {})
    except FileNotFoundError:
        return {}

def load_pdf(file_path: str) -> str:
    try:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Could not load PDF: {str(e)}"