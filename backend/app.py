import os
import shutil
import json
from pathlib import Path
from flask import Flask, request, render_template, abort, send_from_directory, jsonify

from werkzeug.utils import secure_filename

from resume_agent.graph_agent import run_resume_agent


# -------------------------------------------------------------------
# 1. BASE PATHS 
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent        # backend/
STATIC_DIR = BASE_DIR / "static"                  # backend/static/

UPLOAD_DIR = STATIC_DIR / "uploads"
GENERATED_DIR = STATIC_DIR / "generated_resumes"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# 2. Flask App Setup
# -------------------------------------------------------------------
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB limit

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


# -------------------------------------------------------------------
# 3. Web UI
# -------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        file = request.files.get("resume_file")
        jd_text = request.form.get("job_description", "")

        if not file or file.filename == "":
            return render_template("home.html", error="Upload a resume first.")

        if not allowed_file(file.filename):
            return render_template("home.html", error="Only PDF/DOCX allowed.")

        # --- SAVE UPLOADED FILE ---
        filename = secure_filename(file.filename)
        save_path = UPLOAD_DIR / filename
        file.save(save_path)



        try:

            out = run_resume_agent(
                                        str(save_path),
                                        jd_text,
                                        output_dir=str(GENERATED_DIR),
                                        static_dir=str(STATIC_DIR)
                                    )

            pdf_path = out.get("pdf_path")
            pdf_name = None



            if pdf_path:
                src = Path(pdf_path)
                dst = GENERATED_DIR / src.name

                if src.resolve() != dst.resolve():
                    shutil.copy(src, dst)

                pdf_name = dst.name

            # ------------------------
            # PASS DATA TO TEMPLATE
            # ------------------------
            return render_template(
                "home.html",
                result={
                    "candidate": out.get("candidate"),
                    "ats_result": out.get("ats_result"),
                    "structured_resume": out.get("structured_resume"),
                    "pdf_name": pdf_name
                }
            )

        except Exception as e:
            return render_template("home.html", error=f"Processing failed: {e}")

    return render_template("home.html")

# -------------------------------------------------------------------
# 4. Download Route 
# -------------------------------------------------------------------
@app.route("/download/<path:filename>")
def download_file(filename):
    file_path = GENERATED_DIR / filename
    if not file_path.exists():
        abort(404)
    return send_from_directory(GENERATED_DIR, filename, as_attachment=True)




# -------------------------------------------------------------------
# 5. Final  POST API Route
# -------------------------------------------------------------------

@app.route("/api/generate_resume", methods=["POST"])
def api_generate_resume():
    file = request.files.get("resume_file")
    jd_text = request.form.get("job_description", "")

    if not file:
        return jsonify({"status": "error", "message": "resume_file is required"}), 400

    if not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Only PDF/DOCX allowed"}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    save_path = UPLOAD_DIR / filename
    file.save(save_path)

    try:
        out = run_resume_agent(
            str(save_path),
            jd_text,
            output_dir=str(GENERATED_DIR),
            static_dir=str(STATIC_DIR)
        )

        pdf_path = out.get("pdf_path")
        pdf_name = Path(pdf_path).name

        pdf_url = request.host_url + "download/" + pdf_name

        return jsonify({
            "status": "success",
            "candidate": out.get("candidate"),
            "structured_resume": out.get("structured_resume"),
            "ats_result": out.get("ats_result"),
            "pdf_url": pdf_url
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500




# -------------------------------------------------------------------
# 6. Run Server
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
