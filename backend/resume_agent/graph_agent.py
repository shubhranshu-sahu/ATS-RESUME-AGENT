"""
graph_agent.py — clean LangGraph orchestration for the Resume Agent.

Pipeline:
    parse_resume_tool
        → structured_resume_tool
        → jd_parser_tool
        → ats_and_jd_match_tool
        → resume_enhance_and_build_tool

"""

import json
from typing import Dict, Any

from langgraph.graph import StateGraph, END

# --- Import your tools normally (no try/except) ---
from resume_agent.parser import parse_resume_tool
from resume_agent.structured_extractor import structured_resume_tool
from resume_agent.jd_parser import jd_parser_tool
from resume_agent.ats_evaluator import ats_and_jd_match_tool
from resume_agent.resume_builder import resume_enhance_and_build_tool


# -------------------- STATE --------------------


from typing import TypedDict, Optional, Dict, Any

class ResumeState(TypedDict, total=False):
    """
    State shared across nodes for LangGraph.
    """
    resume_path: str
    jd_text: str

    # New fields for HTML/PDF generation
    static_dir: Optional[str]      # contains resume_template.html & resume.css
    output_dir: Optional[str]      # where PDF is saved

    # Intermediate results
    parsed_resume: Dict[str, Any]
    structured_resume: Dict[str, Any]
    jd_info: Dict[str, Any]
    ats_result: Dict[str, Any]
    builder_result: Dict[str, Any]




# -------------------- NODES --------------------

def node_parse_resume(state: ResumeState) -> ResumeState:
    out = parse_resume_tool.run({"file_path": state["resume_path"]})
    state["parsed_resume"] = out
    return state


def node_extract_structure(state: ResumeState) -> ResumeState:
    raw_text = state["parsed_resume"].get("raw_text", "")
    hyperlinks = state["parsed_resume"].get("metadata", {}).get("hyperlinks", [])

    out = structured_resume_tool.run({
        "data": {
            "raw_text": raw_text,
            "hyperlinks": hyperlinks
        }
    })

    # tool returns {"structured_resume": {...}}
    state["structured_resume"] = out.get("structured_resume", {})
    return state


def node_parse_jd(state: ResumeState) -> ResumeState:
    out = jd_parser_tool.run({"jd_text": state["jd_text"]})
    state["jd_info"] = out.get("jd_info", {})
    return state


def node_compute_ats(state: ResumeState) -> ResumeState:
    out = ats_and_jd_match_tool.run({
        "structured_resume": state["structured_resume"],
        "jd_info": state["jd_info"]
    })
    state["ats_result"] = out
    return state


def node_enhance_and_build(state: ResumeState) -> ResumeState:
    out = resume_enhance_and_build_tool.run({
        "structured_resume": state["structured_resume"],
        "jd_info": state["jd_info"],
        "missing_keywords": state["ats_result"].get("missing_keywords", []),
        "template_path": state.get("template_path"),
        "static_dir": state.get("static_dir"),
        "output_dir": state.get("output_dir") 
    })
    state["builder_result"] = out
    return state


# -------------------- BUILD GRAPH --------------------

workflow = StateGraph(ResumeState)

# Add nodes
workflow.add_node("parse_resume", node_parse_resume)
workflow.add_node("extract_structure", node_extract_structure)
workflow.add_node("parse_jd", node_parse_jd)
workflow.add_node("compute_ats", node_compute_ats)
workflow.add_node("enhance_and_build", node_enhance_and_build)

# Edges
workflow.set_entry_point("parse_resume")
workflow.add_edge("parse_resume", "extract_structure")
workflow.add_edge("extract_structure", "parse_jd")
workflow.add_edge("parse_jd", "compute_ats")
workflow.add_edge("compute_ats", "enhance_and_build")
workflow.add_edge("enhance_and_build", END)

# Compile
graph = workflow.compile()


# -------------------- RUNNER FUNCTION --------------------

def run_resume_agent(
    resume_path: str,
    jd_text: str,
    static_dir: str | None = None,
    output_dir: str | None = None
) -> Dict[str, Any]:
    """
    Runs the LangGraph pipeline and returns final JSON-friendly results.

    static_dir  → where template.html + resume.css are stored
    output_dir  → where final PDF is saved
    """

    initial_state = ResumeState({
        "resume_path": resume_path,
        "jd_text": jd_text,
        "static_dir": static_dir,
        "output_dir": output_dir,
    })

    final_state = graph.invoke(initial_state)

    return {
        "candidate": final_state.get("structured_resume", {}).get("name"),
        "structured_resume": final_state.get("structured_resume"),
        "improved_structured_resume": final_state.get("builder_result", {}).get("improved_structured_resume"),
        "ats_result": final_state.get("ats_result"),
        "pdf_path": final_state.get("builder_result", {}).get("pdf_path"),
    }



# -------------------- CLI TEST --------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", "-r", required=True)
    parser.add_argument("--jd", "-j", required=False, default="")
    parser.add_argument("--template", "-t", required=False, default=None)
    args = parser.parse_args()

    out = run_resume_agent(args.resume, args.jd, args.template)
    print(json.dumps(out, indent=2, ensure_ascii=False))

