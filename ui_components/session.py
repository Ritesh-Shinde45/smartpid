import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

try:
    from services import db
    if not all(hasattr(db, f) for f in ("init_db", "list_projects", "create_project")):
        db = None
except ImportError:
    db = None

DEFAULT_PROJECT = "Demo Project"


def load_json(relative_path: str, default=None):
    """Read a JSON file relative to the project root."""
    path = ROOT / relative_path
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def init_state() -> None:
    if "initialised" in st.session_state:
        return

    if db is not None:
        db.init_db()

    st.session_state.update(
        {
            "initialised": True,
            "project_name": DEFAULT_PROJECT,
            "session_projects": [DEFAULT_PROJECT],
            # Config loaded from /config (data, not code)
            "hardware": load_json(
                "config/hardware.json",
                {"cioc_per_cabinet": 4, "baseplates_per_cioc": 8, "charms_per_baseplate": 12},
            ),
            "rules": load_json("config/default_rules.json", []),
            # Pipeline data
            "signals_df": None,
            "column_mapping": None,
            "allocation": None,
            "violations": None,
            "tqs": None,
            "report_ready": False,
            "rev_b_df": None,
            "rev_b_allocation": None,
            "impact_report": None,
        }
    )


def list_projects() -> list:
    if db is not None:
        names = db.list_projects()
        if names:
            return names
    return st.session_state["session_projects"]


def create_project(name: str) -> None:
    if db is not None:
        db.create_project(name)
    if name not in st.session_state["session_projects"]:
        st.session_state["session_projects"].append(name)
    set_active_project(name)


def set_active_project(name: str) -> None:
    st.session_state["project_name"] = name
    for key in (
        "signals_df", "column_mapping", "allocation", "violations",
        "tqs", "rev_b_df", "rev_b_allocation", "impact_report",
    ):
        st.session_state[key] = None
    st.session_state["report_ready"] = False


def llm_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))