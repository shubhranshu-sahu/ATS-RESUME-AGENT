# ATS Resume Agent

ATS Resume Agent is an AI-powered backend utility built to evaluate, parse, and enhance resumes using Large Language Models (LLMs). It extracts structured data from PDF or DOCX resumes and compares them with a given Job Description (JD) to generate a detailed ATS report, suggestions, keyword match percentage, and enhanced resume output.


---

## Overview

This project focuses on automating resume processing using an intelligent backend pipeline. The system provides:

- Resume parsing (PDF/DOCX)
- Job description comparison
- ATS score calculation
- Missing keyword detection
- Resume improvement suggestions
- Structured JSON output via REST API

The system currently exposes a **single POST API endpoint** that accepts resume and JD inputs and returns a JSON response.

---

## Features

- Extracts text and metadata from PDF and DOCX resumes
- LLM-powered structured resume extraction (skills, projects, education, experience, links)
- ATS score calculation based on structure, keyword match, formatting, and relevancy
- Job description comparison with missing/weak areas highlighted
- Returns structured JSON output
- Extracts and stores links (GitHub, LinkedIn, portfolios, etc.)

---

## Tech Stack

| Component | Technology |
|----------|------------|
| Backend | Python (FLASK) |
| AI/LLM | Gemini API  |
| Parsing | PyMuPDF (`fitz`), `python-docx` |
| Validation | Pydantic Models |
| Output Options | JSON responses |

---

## API Documentation

### `POST /generate_resume`

Accepts a resume file (PDF/DOCX) and optional job description text.

#### Request Body (multipart/form-data):

```
resume: <PDF or DOCX file>
jd_text: <String> (optional)
```

#### Example Response:

```json

{
    "ats_result": {
        "ats_score": 55,
        "jd_match": 78,
        "missing_keywords": [
            "Java", "Go", "GitHub", "Linux", "GCP", "AWS", "Azure" ],
        "suggestions": [
            "**Add a Professional Summary:** Include a concise summary at the top of your resume. Highlight your key technical skills (Python, Flask, NodeJS, Data Structures & Algorithms, API development, full-stack experience) and explicitly state your interest in 'Software Engineering Intern' roles, potentially mentioning 'backend engineering' to align with the JD.",
            "**Quantify Achievements:** For your experience bullet points, quantify your impact where possible. For example, instead of 'Debbuged the code breaks', consider 'Reduced debugging time by X% through systematic code analysis' or 'Improved API integration efficiency by Y%'.",
            "**Explicitly Mention Soft Skills:** Integrate keywords like 'communication,' 'collaboration,' 'teamwork,' and 'problem-solving' into your project or experience descriptions. For instance, 'Collaborated with team members to design and implement...' or 'Applied problem-solving skills to overcome technical challenges in...'",
        ]
    },
    "candidate": "SHUBHRANSHU SAHU",
    "pdf_url": "http://192.168.1.4:5000/download/shubhranshu_sahu_resume_1765000964.pdf",
    "status": "success",
    "structured_resume": {
        "achievements": [
            "Academic Achiever in all semesters.",
            "Was in top 1% The Joy of Computing using Python (NPTEL)",
            "Was in top 1% Data Base Management System (NPTEL)"
        ],
        "certifications": [
            {
                "issuer": "FreeCodeCamp",
                "link": "https://www.freecodecamp.org/certification/Shubhranshu_sahu/responsive-web-design",
                "name": "Responsive Web Design",
                "year": 2021
            },
            {
                "issuer": "HackerRank",
                "link": "https://www.hackerrank.com/certificates/91cc6f7ced9d",
                "name": "MySQL (Intermediate)",
                "year": 2025
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Technology, Computer Science Engineering",
                "end_year": 2027,
                "grade": "CGPA : 9.42/10",
                "institution": "Shri Vaishnav Vidyapeeth Vishwavidyalaya, Indore",
                "raw": "2023 - 2027 Shri Vaishnav Vidyapeeth Vishwavidyalaya, Indore Bachelor of Technology, Computer Science Engineering | CGPA : 9.42/10",
                "start_year": 2023,
                "type": "college"
            },
            {
                "degree": "Class XII",
                "end_year": 2023,
                "grade": "Aggregate: 82%",
                "institution": "Shri Devi Ahilya Shishu Vihar, Indore (CBSE)",
                "raw": "2022 - 2023 Shri Devi Ahilya Shishu Vihar, Indore (CBSE) Class XII | Aggregate: 82%",
                "start_year": 2022,
                "type": "school"
            },
            {
                "degree": "Class X",
                "end_year": 2021,
                "grade": "CGPA: 86.8%",
                "institution": "S.I.C.A. Senior Secondary School, Indore (CBSE)",
                "raw": "S.I.C.A. Senior Secondary School, Indore (CBSE) 2020 - 2021 Class X | CGPA: 86.8%",
                "start_year": 2020,
                "type": "school"
            }
        ],
        "email": "shubhranshu2023@gmail.com",
        "experience": [
            {
                "bullets": [
                    "Working on the user interface of Live project (Ananda himalayas) and Integration of Backend using NodeJS, Debbuged the code breaks and testing of API.",
                    "Key Skills: MERN, firebase"
                ],
                "company": "Synapses",
                "duration": "Feb’23 - Present",
                "end_month_year": "Present",
                "end_year": null,
                "location": null,
                "raw": "Synapses | SOFTWARE ENGINEER Feb’23 - Present\n● Working on the user interface of Live project (Ananda himalayas) and Integration of Backend using NodeJS, Debbuged the code\nbreaks and testing of API.\n● Key Skills: MERN, firebase",
                "role": "SOFTWARE ENGINEER",
                "start_month_year": "Feb’23",
                "start_year": 2023
            },
            {
                "bullets": [
                    "Build responsive dashboard using ReactJS and Redux and implemented map-box for drone data visualization.",
                    "Added features of image, video, point cloud visualization and annotation and created API for converting videos into frames.",
                    "Key Skills: React, Redux, MaterialUI, NodeJS"
                ],
                "company": "Vyorius",
                "duration": "Aug’22 - Oct’22",
                "end_month_year": "Oct’22",
                "end_year": 2022,
                "location": null,
                "raw": "Vyorius | FULL STACK DEVELOPER INTERN Aug’22 - Oct’22\n● Build responsive dashboard using ReactJS and Redux and implemented map-box for drone data visualization.\n● Added features of image, video, point cloud visualization and annotation and created API for converting videos into frames.\n● Key Skills: React, Redux, MaterialUI, NodeJS",
                "role": "FULL STACK DEVELOPER INTERN",
                "start_month_year": "Aug’22",
                "start_year": 2022
            }
        ],
        "extracurriculars": [],
        "github": "https://github.com/shubhranshu-sahu/",
        "linkedin": "https://www.linkedin.com/in/shubhranshu-sahu/",
        "name": "SHUBHRANSHU SAHU",
        "other_fields": {},
        "phone": "+91-8964849231",
        "projects": [
            {
                "bullets": [
                    "Developed a full-stack web application to enable students to buy, sell, or donate old NCERT books, promoting educational access and sustainability.",
                    "Built core features like book listings, user login, posting ads, and direct contact between students using Flask and MySQL.",
                    "Designed with a clean and intuitive interface, focusing on local peer-to-peer book exchange without delivery or payment systems."
                ],
                "link": null,
                "raw": "📚 Give & Read – Book Sharing Platform | 2024\nFlask, HTML, CSS, JavaScript, MySQL\n• \nDeveloped a full-stack web application to enable students to buy, sell, or donate old NCERT books, promoting educational\naccess and sustainability.\n• \nBuilt core features like book listings, user login, posting ads, and direct contact between students using Flask and MySQL.\n• \nDesigned with a clean and intuitive interface, focusing on local peer-to-peer book exchange without delivery or payment\nsystems.",
                "tech_stack": [
                    "Flask",
                    "HTML",
                    "CSS",
                    "JavaScript",
                    "MySQL"
                ],
                "title": "Give & Read – Book Sharing Platform",
                "year": 2024
            },
            {
                "bullets": [
                    "Developed a full-stack web platform for MSMEs to log carbon-emitting activities and monitor emissions across categories like fuel, electricity, and transport.",
                    "Built AI-powered module for personalized carbon reduction suggestions based on user data.",
                    "Implemented interactive summaries with charts and downloadable PDF reports with category-wise CO₂ analysis.",
                    "Responsive UI with sidebar navigation, modals, and smooth data visualizations."
                ],
                "link": "https://carbontrack-1mvx.onrender.com/",
                "raw": "🟢 MSME – CarbonTrack | 2025\nFlask, MySQL, HTML/CSS, Bootstrap, Chart.js | Live: carbontrack-1mvx.onrender.com\n• \nDeveloped a full-stack web platform for MSMEs to log carbon-emitting activities and monitor emissions across categories like\nfuel, electricity, and transport.\n• \n Built AI-powered module for personalized carbon reduction suggestions based on user data.\n• \nImplemented interactive summaries with charts and downloadable PDF reports with category-wise CO₂ analysis.\n• \nResponsive UI with sidebar navigation, modals, and smooth data visualizations.",
                "tech_stack": [
                    "Flask",
                    "MySQL",
                    "HTML/CSS",
                    "Bootstrap",
                    "Chart.js"
                ],
                "title": "MSME – CarbonTrack",
                "year": 2025
            }
        ],
        "skills": [
            "Python",
            "Flask",
            "HTML",
            "CSS",
            "JavaScript",
            "MySQL",
            "Pandas",
            "NumPy",
            "Matplotlib",
            "Git",
            "Data Structures & Algorithms",
            "Machine Learning",
            "MERN",
            "Firebase",
            "React",
            "Redux",
            "MaterialUI",
            "NodeJS",
            "Bootstrap",
            "Chart.js"
        ],
        "summary": null,
        "trainings": [
            {
                "description": "Completed beginner-level course",
                "link": null,
                "name": "Python Programming",
                "year": 2023
            }
        ]
    }
}

```

---

## Project Structure

```
ATS-RESUME-AGENT/
│   
│   final_output.pdf
│   sample_JOB_DESCRIPTION.txt
│   test_resume_docx.docx
│   test_resume_pdf.pdf
│
└───backend
    │   .env
    │   app.py
    │
    ├───resume_agent
    │   │   ats_evaluator.py
    │   │   graph_agent.py
    │   │   jd_parser.py
    │   │   parser.py
    │   │   resume_builder.py
    │   │   structured_extractor.py
    │   │   utils.py
    │   │   __init__.py
    │
    ├───static
    │   │   resume.css
    │   │   resume_template.html
    │   │
    │   ├───generated_resumes
    │   │       <generated.pdf files>
    │   │
    │   └───uploads
    │           test_resume_pdf.pdf
    │
    └───templates
            home.html
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Virtual environment tool (optional but recommended)

### Installation

```
git clone https://github.com/shubhranshu-sahu/ATS-RESUME-AGENT
cd ATS-RESUME-AGENT

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Run the backend:

```
python backend/app.py
```

