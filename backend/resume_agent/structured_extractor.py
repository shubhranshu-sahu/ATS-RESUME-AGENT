"""
structured_extractor.py — Convert raw resume text into structured resume
using LLM + Pydantic schema.

This module defines:
- Pydantic resume structure (now includes Experience with date fields)
- LLM extraction prompt (asks specifically for years/dates in projects/certs)
- structured_resume_tool (LangChain Tool)

Drop-in replacement for the previous file: preserves tool name and most variables.
"""
import json
from typing import Dict, Any, List, Literal, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# NOTE: use your shared llm from utils (doesn't change)
from resume_agent.utils import llm


# ----------------------------
# 1. Pydantic schema (extended)
# ----------------------------

class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None
    type: Optional[Literal["school", "college"]] = None
    raw: Optional[str] = None

class Experience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    start_month_year: Optional[str] = None  # e.g. "Jun 2022" or "2022"
    end_month_year: Optional[str] = None    # e.g. "Dec 2023" or "Present"
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    duration: Optional[str] = None          # e.g. "1 yr 6 mos"
    bullets: List[str] = Field(default_factory=list)
    raw: Optional[str] = None

class Project(BaseModel):
    title: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)
    link: Optional[str] = None
    year: Optional[int] = None
    raw: Optional[str] = None

class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    link: Optional[str] = None
    year: Optional[int] = None

class Training(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    link: Optional[str] = None
    year: Optional[int] = None

class StructuredResume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None

    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    extracurriculars: List[str] = Field(default_factory=list)
    trainings: List[Training] = Field(default_factory=list)
    other_fields: Dict[str, Any] = Field(default_factory=dict)


# Create parser
structured_parser = PydanticOutputParser(pydantic_object=StructuredResume)


# ----------------------------
# 2. Prompt template (improved)
# ----------------------------
PROMPT = PromptTemplate(
    template="""
You are an expert resume parser. Convert the resume text and hyperlink list into a clean structured JSON following the schema.

Required fields to extract (if present):
- name, email, phone, linkedin, github
- education: institution, degree, start_year (YYYY), end_year (YYYY), grade, raw
For every education entry, add field `"type"`:
    - "college" if it is a bachelor's / master's / diploma / university
    - "school" if it is Class X, Class XII, High School, CBSE, etc.
- experience: company, role, location, start_month_year (prefer "Mon YYYY" or "YYYY"), end_month_year, start_year, end_year, duration, bullets (list), raw
- projects: title, tech_stack (list), bullets (list), link, year (YYYY if present), raw
- skills: list of short skill strings (no objects)
- certifications: name, issuer, link, year (YYYY if present)
- trainings: name, description, link, year (YYYY if present)
- achievements: list of strings

Rules:
1) Output **ONLY** valid JSON that matches the schema exactly (top-level object corresponds to the Pydantic model).
2) Use null or empty list when a field is missing.
3) For dates prefer full year (YYYY). If you detect "Jun 2022" keep as start_month_year and additionally set start_year=2022.
4) For certifications/projects include year if it appears near the item in the resume text.
5) Preserve original textual fragments in the `raw` fields when possible.
6) Do not hallucinate — if uncertain, use null or empty list.

{format_instructions}

Resume Text:
{resume_text}

Hyperlinks (list):
{hyperlinks}

Return ONLY the JSON (no commentary).
""",
    input_variables=["resume_text", "hyperlinks"],
    partial_variables={"format_instructions": structured_parser.get_format_instructions()}
)


# ----------------------------
# 3. LangChain tool
# ----------------------------
@tool
def structured_resume_tool(data: dict) -> dict:
    """
    Convert raw_text + hyperlinks → structured resume JSON.
    Expected input:
       {"raw_text": "...", "hyperlinks": [...]}
    Returns:
       {"structured_resume": {...}} on success, or {"error":..., "raw": ...}
    """
    raw_text = data.get("raw_text", "")
    hyperlinks = data.get("hyperlinks", [])

    prompt_text = PROMPT.format(
        resume_text=raw_text,
        hyperlinks=json.dumps(hyperlinks, ensure_ascii=False, indent=2)
    )

    llm_out = llm.invoke(prompt_text)
    # llm.invoke may return an object with .content (some SDKs) or a string
    llm_text = llm_out.content if hasattr(llm_out, "content") else llm_out

    try:
        # PydanticOutputParser.parse usually returns a Pydantic model instance.
        parsed = structured_parser.parse(llm_text)
        # Normalize to a plain dict in a forward-compatible way:
        if hasattr(parsed, "model_dump"):
            structured_data = parsed.model_dump()
        elif hasattr(parsed, "dict"):
            # older pydantic
            structured_data = parsed.dict()
        else:
            structured_data = parsed  # assume it's already a dict




        return {"structured_resume": structured_data}
    except Exception as e:
        # Provide raw LLM output for debugging; callers may retry/repair later.
        raw_text_out = llm_text if isinstance(llm_text, str) else str(llm_text)
        return {"error": "LLM returned invalid structure", "raw": raw_text_out, "exception": str(e)}


# ----------------------------
# 4. Self-test
# ----------------------------
if __name__ == "__main__":
    print("\n[structured_extractor.py] Self-test...\n")
    sample_input = {
        "raw_text": "John Doe\nEmail: john@example.com\nJun 2022 - Aug 2023: Software Engineer at Acme Corp\n- Built X\n- Improved Y\nCertifications: Responsive Web Design (FreeCodeCamp) 2023\nProjects: MyApp (Python, Flask) 2022\n",
        "hyperlinks": ["https://github.com/johndoe"]
    }
    out = structured_resume_tool.run({"data": sample_input})
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("\n[structured_extractor.py] Done.\n")

