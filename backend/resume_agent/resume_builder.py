# resume_agent/resume_builder.py
"""
Resume builder — upgraded.

- Pydantic models aligned with structured_extractor (education type, years on projects/certs/experience)
- Keeps original variable names and function signature
- LLM enhance + schema validation + 3x repair attempts
- Post-LLM normalization (grades / date rendering / tech-stack label / caps)
- Renders Jinja HTML template from static_dir and produces ONE-PAGE PDF via Playwright
- Tries to keep final resume to 1 page by trimming bullets, limiting projects to 2 bullets, and shortening summary
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional, List, Literal

from langchain.tools import tool
from pydantic import BaseModel, Field, ValidationError
import jinja2

from resume_agent.utils import llm, strip_fences

# Playwright (sync)
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ---------------------------
# Pydantic models (updated)
# ---------------------------

class ImprovedEducation(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None
    raw: Optional[str] = None
    # new: explicit type to help rendering logic ("school" | "college" | "other")
    type: Optional[Literal["school", "college", "other"]] = None


class ImprovedExperience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    start_month_year: Optional[str] = None  # e.g. "Feb '23"
    end_month_year: Optional[str] = None    # e.g. "Present" or "Oct '23"
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    duration: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)
    raw: Optional[str] = None


class ImprovedProject(BaseModel):
    title: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)
    link: Optional[str] = None
    year: Optional[int] = None
    raw: Optional[str] = None


class ImprovedCertification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    link: Optional[str] = None
    year: Optional[int] = None
    raw: Optional[str] = None


class ImprovedResume(BaseModel):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin: Optional[str]
    github: Optional[str]
    summary: Optional[str]

    education: List[ImprovedEducation] = Field(default_factory=list)
    experience: List[ImprovedExperience] = Field(default_factory=list)
    projects: List[ImprovedProject] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)

    certifications: List[ImprovedCertification] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    extracurriculars: List[str] = Field(default_factory=list)
    trainings: List[dict] = Field(default_factory=list)


# ---------------------------
# Helpers (formatting / trimming)
# ---------------------------

def shorten_summary(text: Optional[str], max_chars: int = 300) -> str:
    if not text:
        return ""
    t = re.sub(r"\s+", " ", text.strip())
    return t[:max_chars].rstrip() + ("..." if len(t) > max_chars else "")


def trim_project_bullets(projects: List[dict], max_bullets: int = 2) -> List[dict]:
    for p in projects:
        if isinstance(p, dict):
            bullets = p.get("bullets", [])
            if isinstance(bullets, list):
                p["bullets"] = bullets[:max_bullets]
    return projects


def normalize_skills(skills: List[Any]) -> List[str]:
    out = []
    for s in (skills or []):
        if isinstance(s, str):
            out.append(s.strip())
        elif isinstance(s, dict) and s.get("name"):
            out.append(str(s.get("name")).strip())
        else:
            out.append(str(s).strip())
    return [s for s in out if s]


def format_education_entry(e: dict) -> dict:
    """
    Prepare display-friendly fields:
    - Clean grade and remove LLM-added prefixes
    - Consistent prefix: CGPA for college, Grade for school
    - Build years_display
    """
    out = dict(e)

    # --------------------------
    # 1. Decide type (if missing)
    # --------------------------
    etype = out.get("type")
    if not etype:
        deg = (out.get("degree") or "").lower()
        raw = (out.get("raw") or "").lower()

        if any(x in deg for x in ["class x", "class xi", "class xii"]) or "cbse" in raw:
            etype = "school"
        elif deg:
            etype = "college"
        else:
            etype = "other"

        out["type"] = etype

    # --------------------------
    # 2. CLEAN GRADE VALUE
    # --------------------------
    grade = out.get("grade")

    if grade:
        # Remove unwanted prefixes like:
        # "CGPA: 9.2", "Grade - 85%", "Aggregate: 82%", "Percentage: 91%"
        grade_clean = re.sub(
            r"^(cgpa|grade|aggregate|agg|percentage|percent|score)\s*[:\-]\s*",
            "",
            grade,
            flags=re.I
        ).strip()

        # Also remove trailing "%" spaces like "82% " → "82%"
        grade_clean = grade_clean.replace("Aggregate", "").strip()

        out["grade"] = grade_clean

        # Add our OWN prefix
        if etype == "college":
            out["grade_label"] = f"CGPA: {grade_clean}"
        elif etype == "school":
            out["grade_label"] = f"Grade: {grade_clean}"
        else:
            out["grade_label"] = grade_clean
    else:
        out["grade_label"] = None


    # --------------------------
    # 3. YEARS DISPLAY
    # --------------------------
    sy = out.get("start_year")
    ey = out.get("end_year")

    if sy and ey:
        out["years_display"] = f"{sy}–{ey}"
    elif sy and not ey:
        out["years_display"] = f"{sy}–"
    elif ey and not sy:
        out["years_display"] = f"–{ey}"
    else:
        out["years_display"] = ""

    return out



def format_experience_entry(exp: dict) -> dict:
    # ensure bullets are strings and limit bullets to 3 to keep 1-page
    e = dict(exp)
    bullets = e.get("bullets") or []
    # flatten any non-str bullets
    new_b = []
    for b in bullets:
        if isinstance(b, str):
            new_b.append(b.strip())
        elif isinstance(b, dict) and b.get("text"):
            new_b.append(b.get("text").strip())
        else:
            new_b.append(str(b).strip())
    e["bullets"] = new_b[:2]  # limit to 2 bullets
    # format date display
    sm = e.get("start_month_year") or ""
    em = e.get("end_month_year") or ""
    if sm or em:
        e["dates_display"] = f"{sm} – {em}".strip(" – ")
    else:
        # fallback to years
        sy = e.get("start_year")
        ey = e.get("end_year")
        if sy and ey:
            e["dates_display"] = f"{sy}–{ey}"
        elif sy and not ey:
            e["dates_display"] = f"{sy}–"
        elif ey:
            e["dates_display"] = f"–{ey}"
        else:
            e["dates_display"] = ""
    return e


def format_project_entry(p: dict) -> dict:
    out = dict(p)
    # tech stack rendering prefix
    tech = out.get("tech_stack") or []
    if isinstance(tech, list):
        out["tech_display"] = "Tech Stack: " + ", ".join([str(t).strip() for t in tech]) if tech else ""
    else:
        out["tech_display"] = f"Tech Stack: {str(tech)}"
    # year display if present
    if out.get("year"):
        out["year_display"] = str(out.get("year"))
    else:
        out["year_display"] = ""
    # trim bullets (2 max)
    bullets = out.get("bullets") or []
    out["bullets"] = bullets[:2]
    return out


def format_cert_entry(c: dict) -> dict:
    out = dict(c)
    if out.get("year"):
        out["cert_display"] = f"{out.get('name')} — {out.get('issuer')} ({out.get('year')})"
    else:
        out["cert_display"] = f"{out.get('name')} — {out.get('issuer')}" if out.get("issuer") else out.get("name")
    return out


# ---------------------------
# Main tool (signature unchanged)
# ---------------------------

@tool
def resume_enhance_and_build_tool(
    structured_resume: dict,
    jd_info: Optional[dict] = None,
    missing_keywords: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    static_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enhances resume → renders Jinja HTML → Playwright PDF (1 page)
    """

    # ---------- 1) LLM enhance with schema + auto-repair ----------
    prompt = f"""
You are a senior resume editor. Improve this resume JSON for hiring audiences and ATS.

Return ONLY a JSON object with top-level key "improved" whose value follows this schema:
- name, email, phone, linkedin, github, summary
- education: list with institution, degree, start_year, end_year, grade, type (school|college|other), raw
- experience: list with company, role, start_month_year, end_month_year, start_year, end_year, bullets (list)
- projects: list with title, tech_stack (list), bullets (list), year
- certifications: list with name, issuer, link, year
- The `achievements` field MUST remain a non-empty list IF the input resume contains achievements.
- The `skills` field MUST remain a non-empty list IF the input resume contains skills.


structured_resume = {json.dumps(structured_resume, ensure_ascii=False, indent=2)}
jd_info = {json.dumps(jd_info or {}, ensure_ascii=False, indent=2)}
missing_keywords = {json.dumps(missing_keywords or [], ensure_ascii=False)}

Rules:
- Return ONLY valid JSON.
- The JSON must be: {{ "improved": {{ ... }} }}
- skills and arrays must be arrays of strings.
- Keep project bullets <= 2, experience bullets <= 2, summary <= 300 chars.
"""

    attempt = 0
    improved = None
    llm_raw = None

    while attempt < 3:
        attempt += 1
        resp = llm.invoke(prompt)
        llm_raw = resp.content if hasattr(resp, "content") else resp
        clean = strip_fences(llm_raw)

        try:
            parsed = json.loads(clean)
            if "improved" not in parsed:
                raise ValueError("missing top-level 'improved'")
            validated = ImprovedResume.model_validate(parsed["improved"])
            improved = validated.model_dump()
            # --- HARD FAIL-SAFE: Restore lost sections if LLM removed them ---
            if structured_resume.get("skills") and not improved.get("skills"):
                improved["skills"] = structured_resume["skills"]

            if structured_resume.get("achievements") and not improved.get("achievements"):
                improved["achievements"] = structured_resume["achievements"]

            break
        except Exception as e:
            prompt = f"""
Your previous output was invalid or did not match the schema.

Error:
{e}

Previous output:
{clean}

Fix the JSON and return ONLY:
{{ "improved": {{ ... }} }}
"""
            continue

    if improved is None:
        # fallback — accept structured_resume as-is but normalize shapes
        improved = structured_resume

    # ---------- 2) Post-LLM normalization / safety ----------
    # summary trimming (we'll keep but not render it but still keep accessible)
    improved["summary"] = shorten_summary(improved.get("summary", ""))

    # normalize skills
    improved["skills"] = normalize_skills(improved.get("skills", []))

    # Trim project bullets and normalize projects entries
    projects = improved.get("projects", []) or []
    projects = trim_project_bullets(projects, max_bullets=2)
    projects = [format_project_entry(p if isinstance(p, dict) else {"title": str(p)}) for p in projects]
    improved["projects"] = projects

    # Normalize experience entries
    exps = improved.get("experience", []) or []
    exps = [format_experience_entry(e if isinstance(e, dict) else {"company": str(e)}) for e in exps]
    improved["experience"] = exps[0:2] # limit experience to first 2 entries to save space

    # Normalize education
    eds = improved.get("education", []) or []
    eds = [format_education_entry(e if isinstance(e, dict) else {"institution": str(e)}) for e in eds]
    improved["education"] = eds

    # Certifications formatting
    certs = improved.get("certifications", []) or []
    certs = [format_cert_entry(c if isinstance(c, dict) else {"name": str(c)}) for c in certs]
    improved["certifications"] = certs

    # Achievements/training keep as-is but limit total count to avoid overflow
    improved["achievements"] = (improved.get("achievements") or [])[:3]
    improved["trainings"] = (improved.get("trainings") or [])[:4]

    # print(improved)  #------------------------------------------------------------Debug print-----------------------------

    # ---------- 3) Template load & render ----------
    if not static_dir:
        raise ValueError("static_dir must be provided (path to templates + CSS)")
    static_dir = Path(static_dir)

    template_name = "resume_template.html"
    css_name = "resume.css"

    template_path = static_dir / template_name
    css_path = static_dir / css_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Load template and CSS and inline CSS so Playwright sees it
    with open(template_path, "r", encoding="utf-8") as f:
        template_html = f.read()
    with open(css_path, "r", encoding="utf-8") as f:
        css_text = f.read()

    html_with_css = template_html.replace("</head>", f"<style>{css_text}</style></head>")

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(static_dir)))
    template = env.from_string(html_with_css)
    rendered_html = template.render(resume=improved)
#-----------------------------------------------------------------------------
    # print(rendered_html)
#-----------------------------------------------------------------------------

    # ---------- 4) Produce PDF (1 page) ----------
    if not output_dir:
        raise ValueError("output_dir must be provided")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^a-z0-9]+", "_", (improved.get("name") or "candidate").lower())
    ts = int(time.time())
    pdf_path = out_dir / f"{safe_name}_resume_{ts}.pdf"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(no_viewport=True)
            # page.set_viewport_size({"width": 1280, "height": 3000})

            # set html content and wait
            page.set_content(rendered_html, wait_until="networkidle")
            page.emulate_media(media="print")   # ← ENSURE @page CSS WORKS

            # Force one-page PDF with small margins; you may tune margins in CSS too
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                # margin={"top": "0.35in", "bottom": "0.35in", "left": "0.35in", "right": "0.35in"}
                prefer_css_page_size=True 
            )
            browser.close()
    except PlaywrightTimeoutError as e:
        return {"improved_structured_resume": improved, "pdf_path": None, "error": f"Playwright timeout: {e}"}
    except Exception as e:
        return {"improved_structured_resume": improved, "pdf_path": None, "error": f"Playwright error: {e}"}

    # Success
    return {"improved_structured_resume": improved, "pdf_path": str(pdf_path)}

