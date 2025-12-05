"""
ats_evaluator.py — Computes ATS score + JD match + missing keywords
using LLM reasoning over structured resume + JDInfo.

Defines:
- ATSResult schema
- ats_and_jd_match_tool (LangChain tool)
"""

from resume_agent.utils import llm, strip_fences


import json
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI




# ----------------------------------------------------
# 1. ATS Result Schema
# ----------------------------------------------------

class ATSResult(BaseModel):
    ats_score: int = Field(default=0)
    jd_match: int = Field(default=0)
    missing_keywords: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


# ----------------------------------------------------
# 2. Build Prompt Template
# ----------------------------------------------------

ATS_PROMPT = """
You are an ATS scoring expert and recruiter AI.

Evaluate the candidate's resume against the job description.

INPUT RESUME (structured JSON):
{resume_json}

INPUT JOB DESCRIPTION (structured JSON):
{jd_json}

Your tasks:
1. Identify ALL missing / weak keywords.
2. Score ATS compatibility from 0–100.
3. Score JD match relevance from 0–100.
4. Provide actionable suggestions for improvement.

Return ONLY valid JSON:
{{
  "ats_score": 0,
  "jd_match": 0,
  "missing_keywords": [],
  "suggestions": []
}}
"""


# ----------------------------------------------------
# 3. LangChain Tool: ats_and_jd_match_tool
# ----------------------------------------------------

@tool
def ats_and_jd_match_tool(structured_resume: Dict[str, Any], jd_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute ATS and JD match scoring using LLM reasoning.
    """
    prompt = ATS_PROMPT.format(
        resume_json=json.dumps(structured_resume, indent=2),
        jd_json=json.dumps(jd_info, indent=2)
    )

    llm_out = strip_fences(llm.invoke(prompt).content)

    # Try JSON parse
    try:
        parsed = json.loads(llm_out)
        validated = ATSResult(**parsed)
        return validated.model_dump()
    except Exception:
        return {"error": "Bad ATS JSON", "raw": llm_out}


# ----------------------------------------------------
# 4. SELF-TEST
# ----------------------------------------------------

if __name__ == "__main__":
    print("\n[ats_evaluator.py] Self-test running...\n")

    sample_resume = {
        "name": "John Doe",
        "skills": ["Python", "Flask", "Git"],
        "projects": [
            {"title": "API System", "tech_stack": ["Python", "Flask"]}
        ]
    }

    sample_jd = {
        "role_title": "Backend Intern",
        "programming_languages": ["Python", "Java"],
        "frameworks_tools": ["Flask", "Django"],
        "concepts": ["REST APIs", "SQL"],
        "responsibilities": ["Build APIs", "Write clean code"],
        "keywords": ["backend", "APIs", "Python"]
    }

    result = ats_and_jd_match_tool.run({
        "structured_resume": sample_resume,
        "jd_info": sample_jd
    })

    print("ATS Evaluation:\n")
    print(json.dumps(result, indent=2))

    print("\n[ats_evaluator.py] Self-test complete.\n")
