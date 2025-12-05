"""
jd_parser.py — Convert a Job Description text into structured JDInfo
using Gemini + LangChain + Pydantic V2.

Defines:
- JDInfo Pydantic model
- JD parsing prompt template
- jd_parser_tool (LangChain tool)
"""

from resume_agent.utils import llm


import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI



# ----------------------------------------------------
# 1. Pydantic Schema for JD Information
# ----------------------------------------------------

class JDInfo(BaseModel):
    role_title: str = Field(default="", description="Role name if mentioned")
    programming_languages: List[str] = Field(default_factory=list)
    frameworks_tools: List[str] = Field(default_factory=list)
    concepts: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    seniority_level: str = Field(default="", description="Intern, Junior, Mid, Senior")


# LangChain Pydantic parser
jd_parser = PydanticOutputParser(pydantic_object=JDInfo)


# ----------------------------------------------------
# 2. Prompt Template
# ----------------------------------------------------

JD_PROMPT = PromptTemplate(
    template="""
You are an expert HR & Technical Recruiter AI.
Extract structured information from the following Job Description.

{format_instructions}

Job Description:
{jd_text}

Rules:
- Return ONLY valid JSON following the schema.
- Do NOT output any text outside the JSON.
""",
    input_variables=["jd_text"],
    partial_variables={
        "format_instructions": jd_parser.get_format_instructions()
    }
)


# ----------------------------------------------------
# 3. LangChain Tool Definition
# ----------------------------------------------------

@tool
def jd_parser_tool(jd_text: str) -> Dict[str, Any]:
    """Parse a job description text into a structured JDInfo JSON."""
    
    prompt_text = JD_PROMPT.format(jd_text=jd_text)

    # LLM call
    llm_output = llm.invoke(prompt_text).content

    # Try Pydantic validation
    try:
        validated = jd_parser.parse(llm_output)
        return {"jd_info": validated.model_dump()}
    except Exception:
        # Return raw output for debugging
        return {
            "error": "Invalid JD JSON",
            "raw": llm_output
        }


# ----------------------------------------------------
# 4. SELF-TEST
# ----------------------------------------------------

if __name__ == "__main__":
    print("\n[jd_parser.py] Self-test running...\n")

    TEST_JD = """
    Google is seeking Software Engineering Interns.

    Required:
    - Python, Java, Go
    - REST APIs, SQL/NoSQL
    - Data Structures and Algorithms

    Responsibilities:
    - Build scalable backend systems
    - Maintain clean and testable code
    """

    result = jd_parser_tool.run({"jd_text": TEST_JD})

    print("Parsed JD Output:\n")
    print(json.dumps(result, indent=2))

