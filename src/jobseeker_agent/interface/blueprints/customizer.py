import json
import markdown
import re
import threading
from flask import (
    Blueprint,
    render_template,
    send_from_directory,
    jsonify,
    request,
)
from jobseeker_agent.interface import state
from jobseeker_agent.interface.utils import compile as compile_utils
from jobseeker_agent.interface.tasks import customizer_tasks
from jobseeker_agent.utils.paths import (
    get_data_path,
    load_prompt,
    load_cv_template,
    load_reviews,
)

bp = Blueprint("customizer", __name__)


@bp.route("/apply/<int:job_id>")
def apply_for_job(job_id: int):
    """Sets the job_id for the customizer interface and renders the dashboard."""
    print(f"--- Customizer: Received request to apply for job_id: {job_id} ---")
    state.JOB_ID = job_id
    print(f"Customizer state JOB_ID set to: {state.JOB_ID}")
    return render_template("customizer/dashboard.html")


@bp.route("/save-highlights", methods=["POST"])
def save_highlights():
    """Saves the highlighted texts to a JSON file."""
    data = request.get_json()
    highlight_list = data.get("highlights")
    if highlight_list is None:
        return jsonify({"success": False, "error": "No data provided"}), 400

    try:
        output_file = get_data_path() / "resume" / str(state.JOB_ID) / "highlights.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(highlight_list, f, indent=4, ensure_ascii=False)
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/")
def dashboard():
    """Renders the main dashboard HTML."""
    return render_template("customizer/dashboard.html")


@bp.route("/favicon.ico")
def favicon():
    return "", 204


@bp.route("/save-tex", methods=["POST"])
def save_tex():
    """Saves the edited TeX content and recompiles."""
    data = request.get_json()
    content = data.get("content")
    if content is None:
        return jsonify({"success": False, "error": "No content provided"}), 400

    tex_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
    try:
        tex_file.write_text(content, encoding="utf-8")
        success, error_log = compile_utils.compile_tex()
        if success:
            return jsonify({"success": True})
        else:
            return jsonify(
                {"success": False, "error": f"Compilation failed:\n{error_log}"}
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/recompile-tex", methods=["POST"])
def recompile_tex():
    """Just recompiles the existing TeX file."""
    try:
        success, error_log = compile_utils.compile_tex()
        if success:
            return jsonify({"success": True})
        else:
            return jsonify(
                {"success": False, "error": f"Compilation failed:\n{error_log}"}
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/reinitialize-tex", methods=["POST"])
def reinitialize_tex():
    """Resets the TeX file to the original template and recompiles."""
    try:
        template_content = load_cv_template()
        tex_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        tex_file.write_text(template_content, encoding="utf-8")

        success, error_log = compile_utils.compile_tex()
        if success:
            return jsonify({"success": True, "content": template_content})
        else:
            return jsonify(
                {"success": False, "error": f"Compilation failed:\n{error_log}"}
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/update-title", methods=["POST"])
def update_title():
    """Finds and replaces the title in the resume.tex file."""
    data = request.get_json()
    new_title = data.get("title")
    if not new_title:
        return jsonify({"success": False, "error": "No title provided"}), 400

    try:
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        content = resume_file.read_text(encoding="utf-8")

        new_content, count = re.subn(
            r"(\\textbf{\\LARGE )(.*?)(\})",
            r"\\textbf{\\LARGE " + new_title + r"}",
            content,
            count=1,
        )

        if count == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "\\textbf{\\LARGE ...} tag not found in resume.tex",
                    }
                ),
                404,
            )
        resume_file.write_text(new_content, encoding="utf-8")

        compile_success, compile_log = compile_utils.compile_tex()
        if not compile_success:
            resume_file.write_text(content, encoding="utf-8")
            return (
                jsonify(
                    {"success": False, "error": f"PDF recompilation failed: {compile_log}"}
                ),
                500,
            )

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/run-executor", methods=["POST"])
def run_executor():
    """Runs the keyword executor script."""
    try:
        print("Running keyword executor...")
        job_dir = get_data_path() / "resume" / str(state.JOB_ID)
        report_file = job_dir / "insertion_report.json"
        tex_output_file = job_dir / "resume_with_insertion.tex"

        # Check if cached files exist
        if report_file.exists() and tex_output_file.exists():
            print("✅ Found cached report and TeX file. Loading from cache.")
            with open(report_file, "r", encoding="utf-8") as f:
                report = json.load(f)
            new_resume = tex_output_file.read_text(encoding="utf-8")
        else:
            print("ℹ️ No cache found. Calling LLM.")
            keywords_file = job_dir / "keywords_validated.json"
            with open(keywords_file, "r", encoding="utf-8") as f:
                instructions = json.load(f)

            resume_file = job_dir / "resume.tex"
            resume_content = resume_file.read_text(encoding="utf-8")

            profil_pro = load_prompt("profil_pro")
            model = "gpt-5-mini"

            response = customizer_tasks.execute_keywords(
                state.JOB_DESCRIPTION,
                profil_pro,
                resume_content,
                instructions,
                model=model,
            )
            new_resume = response["resume"]
            report = response["report"]

            # Save to cache
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
            tex_output_file.write_text(new_resume, encoding="utf-8")

        # Update the main resume file and recompile
        resume_file = job_dir / "resume.tex"
        resume_file.write_text(new_resume, encoding="utf-8")

        compile_success, compile_log = compile_utils.compile_tex()
        if not compile_success:
            # If compilation fails, add the error to the report instead of raising
            report.append("--- PDF COMPILATION FAILED ---")
            report.append(compile_log)

        print("✅ [SERVER] Process complete. Sending JSON response to browser...")
        response = jsonify({"success": True, "report": report})
        print(f"✅ [SERVER] Response object: {response.get_data(as_text=True)}")
        return response

    except FileNotFoundError:
        print("❌ [SERVER] FileNotFoundError caught. keywords_validated.json likely missing.")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "keywords_validated.json not found. Please finalize keywords first.",
                }
            ),
            404,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/start-extraction", methods=["POST"])
def start_extraction():
    """Starts the keyword extraction in a background thread."""
    job_dir = get_data_path() / "resume" / str(state.JOB_ID)
    titles_file = job_dir / "titles.json"
    keywords_file = job_dir / "keywords.json"

    if titles_file.exists() and keywords_file.exists():
        print("✅ Keyword and title files already exist. Skipping extraction.")
        state.EXTRACTION_STATUS = {"status": "complete", "error": None}
        return jsonify({"status": "complete"})

    if state.EXTRACTION_THREAD is None or not state.EXTRACTION_THREAD.is_alive():
        print("Starting keyword extraction thread...")
        state.EXTRACTION_THREAD = threading.Thread(target=customizer_tasks.run_keyword_extraction_task)
        state.EXTRACTION_THREAD.daemon = True
        state.EXTRACTION_THREAD.start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@bp.route("/extraction-status")
def extraction_status():
    """Checks the status of the keyword extraction."""
    return jsonify(state.EXTRACTION_STATUS)


@bp.route("/start-initial-load", methods=["POST"])
def start_initial_load():
    """Starts the initial data loading in a background thread."""
    if state.DATA_LOADING_THREAD is None or not state.DATA_LOADING_THREAD.is_alive():
        if state.DATA_LOADING_STATUS["status"] == "complete":
            return jsonify({"status": "complete"})

        print("Starting initial data load thread...")
        state.DATA_LOADING_THREAD = threading.Thread(target=customizer_tasks.run_initial_load_task)
        state.DATA_LOADING_THREAD.daemon = True
        state.DATA_LOADING_THREAD.start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@bp.route("/initial-load-status")
def initial_load_status():
    """Checks the status of the initial data load."""
    if state.DATA_LOADING_STATUS["status"] == "complete":
        job_dir = get_data_path() / "resume" / str(state.JOB_ID)
        job_details_file = job_dir / "job_details.json"
        try:
            with open(job_details_file, "r", encoding="utf-8") as f:
                job_details = json.load(f)
            job_details["id"] = state.JOB_ID  # Add the job_id here

            # Convert description from Markdown to HTML
            if "description" in job_details and job_details["description"]:
                processed_markdown = job_details["description"].replace('**', '## ')
                job_details["description"] = markdown.markdown(processed_markdown)
            
            # Convert synthesis from Markdown to HTML
            if "synthesis" in job_details and job_details["synthesis"]:
                job_details["synthesis"] = markdown.markdown(job_details["synthesis"])

            return jsonify({"status": "complete", "job_details": job_details})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return jsonify(
                {"status": "failed", "error": f"Could not load job details: {e}"}
            )

    return jsonify(state.DATA_LOADING_STATUS)


@bp.route("/start-ranking", methods=["POST"])
def start_ranking():
    """Starts the ranking in a background thread."""
    if state.RANKING_THREAD is None or not state.RANKING_THREAD.is_alive():
        print("Starting ranking thread...")
        state.RANKING_STATUS = {"status": "idle", "error": None}
        state.RANKING_THREAD = threading.Thread(target=customizer_tasks.run_ranker_task)
        state.RANKING_THREAD.daemon = True
        state.RANKING_THREAD.start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@bp.route("/ranking-status")
def ranking_status():
    """Checks the status of the ranking."""
    return jsonify(state.RANKING_STATUS)


@bp.route("/start-introduction", methods=["POST"])
def start_introduction():
    """Starts the introduction suggestion in a background thread."""
    if state.INTRODUCTION_THREAD is None or not state.INTRODUCTION_THREAD.is_alive():
        print("Starting introduction suggestion thread...")
        state.INTRODUCTION_THREAD = threading.Thread(target=customizer_tasks.run_introducer_task)
        state.INTRODUCTION_THREAD.daemon = True
        state.INTRODUCTION_THREAD.start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@bp.route("/introduction-status")
def introduction_status():
    """Checks the status of the introduction suggestion."""
    return jsonify(state.INTRODUCTION_STATUS)


@bp.route("/start-cover-letter", methods=["POST"])
def start_cover_letter():
    """Starts the cover letter generation in a background thread."""
    if state.COVER_LETTER_THREAD is None or not state.COVER_LETTER_THREAD.is_alive():
        print("Starting cover letter generation thread...")
        state.COVER_LETTER_THREAD = threading.Thread(target=customizer_tasks.run_cover_letter_task)
        state.COVER_LETTER_THREAD.daemon = True
        state.COVER_LETTER_THREAD.start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@bp.route("/cover-letter-status")
def cover_letter_status():
    """Checks the status of the cover letter generation."""
    return jsonify(state.COVER_LETTER_STATUS)


@bp.route("/cover-letter-content")
def get_cover_letter_content():
    """Gets the cover letter content from the file."""
    cover_letter_file = get_data_path() / "resume" / str(state.JOB_ID) / "cover-letter.md"
    try:
        if cover_letter_file.exists():
            content = cover_letter_file.read_text(encoding="utf-8")
            return jsonify({"success": True, "content": content})
        else:
            return jsonify({"success": False, "error": "Cover letter not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/save-cover-letter", methods=["POST"])
def save_cover_letter():
    """Saves the cover letter content to the file."""
    data = request.get_json()
    content = data.get("content")
    if content is None:
        return jsonify({"success": False, "error": "No content provided"}), 400

    try:
        cover_letter_file = get_data_path() / "resume" / str(state.JOB_ID) / "cover-letter.md"
        cover_letter_file.write_text(content, encoding="utf-8")
        return jsonify({"success": True, "message": "Cover letter saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/convert-cover-letter-to-pdf", methods=["POST"])
def convert_cover_letter_to_pdf():
    """Converts the markdown cover letter to LaTeX and compiles it to PDF."""
    try:
        from jobseeker_agent.customizer.agents.cover_letter.md_to_tex import markdown_to_latex_cover_letter
        from jobseeker_agent.interface.utils import compile as compile_utils
        
        job_dir = get_data_path() / "resume" / str(state.JOB_ID)
        markdown_file = job_dir / "cover-letter.md"
        tex_file = job_dir / "cover-letter.tex"
        
        if not markdown_file.exists():
            return jsonify({"success": False, "error": "Markdown file not found"}), 404
        
        # Convert markdown to LaTeX
        print("[CONVERT] Converting markdown to LaTeX...")
        markdown_to_latex_cover_letter(markdown_file, tex_file)
        print("[CONVERT] Conversion complete.")
        
        # Compile to PDF
        print("[CONVERT] Compiling LaTeX to PDF...")
        success, log = compile_utils.compile_cover_letter_tex()
        
        if not success:
            return jsonify({"success": False, "error": "PDF compilation failed", "log": log}), 500
        
        print("[CONVERT] PDF generated successfully.")
        return jsonify({"success": True, "message": "Cover letter converted and compiled successfully"})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/introduction-report")
def get_introduction_report():
    """Serves the introduction report JSON file."""
    report_file = (
        get_data_path() / "resume" / str(state.JOB_ID) / "opening_lines.json"
    )
    try:
        return send_from_directory(report_file.parent, report_file.name)
    except FileNotFoundError:
        return jsonify({"error": "Introduction report file not found"}), 404


@bp.route("/save-introduction", methods=["POST"])
def save_introduction():
    """Saves the selected introduction to the resume.tex file."""
    data = request.get_json()
    introduction_text = data.get("introduction")
    if not introduction_text:
        return jsonify({"success": False, "error": "No introduction provided"}), 400

    try:
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        content = resume_file.read_text(encoding="utf-8")

        # The new introduction text, wrapped in LaTeX formatting
        new_introduction_formatted = (
            f"\n\n\\begin{{center}}\n    \\textit{{{introduction_text}}}\n\\end{{center}}\n\n"
        )

        # Regex to replace the content between the title and the Experience section
        # We assume the title is the only \textbf{\LARGE ...} element before \section{Experience}
        pattern = re.compile(
            r"(\\textbf{\\LARGE.*?})((?:.|\n)*?)(\\section{Experience})", re.DOTALL
        )

        def repl(match):
            # The introduction will replace everything between the title and the Experience section
            return match.group(1) + new_introduction_formatted + match.group(3)

        new_content, count = pattern.subn(repl, content, count=1)

        if count == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Could not find the insertion point in resume.tex.",
                    }
                ),
                404,
            )

        resume_file.write_text(new_content, encoding="utf-8")

        compile_success, compile_log = compile_utils.compile_tex()
        if not compile_success:
            # Revert the change if compilation fails
            resume_file.write_text(content, encoding="utf-8")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"PDF recompilation failed: {compile_log}",
                    }
                ),
                500,
            )

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/delete-publications", methods=["POST"])
def delete_publications():
    """Deletes the publications section from the resume.tex file."""
    try:
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        content = resume_file.read_text(encoding="utf-8")

        # Pattern to match the entire Publications section
        # This includes the section header and everything until the next section or \end{resume}
        pattern = re.compile(
            r"\\section{Publications}.*?(?=\\section{|\\end{resume})",
            re.DOTALL
        )

        new_content = pattern.sub("", content)

        if new_content == content:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Publications section not found in resume.tex.",
                    }
                ),
                404,
            )

        resume_file.write_text(new_content, encoding="utf-8")

        compile_success, compile_log = compile_utils.compile_tex()
        if not compile_success:
            # Revert the change if compilation fails
            resume_file.write_text(content, encoding="utf-8")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"PDF recompilation failed: {compile_log}",
                    }
                ),
                500,
            )

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/apply-manual-ranking", methods=["POST"])
def apply_manual_ranking():
    """Applies a manual ranking of experiences to the resume."""
    data = request.get_json()
    experience_order = data.get("experience_order")
    hidden_experiences = data.get("hidden_experiences", [])
    
    if not experience_order or not isinstance(experience_order, list):
        return jsonify({"success": False, "error": "Invalid experience order provided"}), 400
    
    try:
        from jobseeker_agent.customizer.agents.ranker import reorder_experiences
        
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        resume_content = resume_file.read_text(encoding="utf-8")
        
        # Apply the reordering (with hidden experiences)
        updated_content = reorder_experiences(resume_content, experience_order, hidden_experiences)
        resume_file.write_text(updated_content, encoding="utf-8")
        
        # Recompile the PDF
        compile_success, compile_log = compile_utils.compile_tex()
        if not compile_success:
            # Revert the change if compilation fails
            resume_file.write_text(resume_content, encoding="utf-8")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"PDF recompilation failed: {compile_log}",
                    }
                ),
                500,
            )
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/get-current-experience-order", methods=["GET"])
def get_current_experience_order():
    """Parses and returns the current order of experiences from the resume."""
    try:
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        resume_content = resume_file.read_text(encoding="utf-8")
        
        # Experience names and their markers in the .tex file
        experience_markers = {
            "JobseekerAgent": "Job-Seeking Agentic Workflow",
            "CameraCalibration": "Camera Calibration for Autonomous Vehicle",
            "Thales DMS": r"\textbf{Thales DMS}",
            "IBM France": r"\textbf{IBM France}"
        }
        
        # Find the Experience section
        exp_section_pattern = re.compile(
            r"\\section{Experience}(.*?)(?=\\section{|\\end{resume})",
            re.DOTALL
        )
        exp_match = exp_section_pattern.search(resume_content)
        
        if not exp_match:
            return jsonify({"error": "Experience section not found"}), 404
        
        experience_section = exp_match.group(1)
        
        # Find positions of each experience in the section
        positions = {}
        for exp_key, marker in experience_markers.items():
            pos = experience_section.find(marker)
            if pos != -1:
                positions[exp_key] = pos
        
        # Sort by position to get the order
        ordered_experiences = sorted(positions.keys(), key=lambda k: positions[k])
        
        # Detect hidden experiences (those wrapped in \iffalse ... \fi)
        hidden_experiences = []
        for exp_key, marker in experience_markers.items():
            # Check if this experience is within an \iffalse ... \fi block
            pattern = rf"\\iffalse.*?{re.escape(marker)}.*?\\fi"
            if re.search(pattern, experience_section, re.DOTALL):
                hidden_experiences.append(exp_key)
        
        return jsonify({
            "experience_order": ordered_experiences,
            "hidden_experiences": hidden_experiences
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/get-current-skills", methods=["GET"])
def get_current_skills():
    """Parses and returns the current skills from the resume."""
    try:
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        resume_content = resume_file.read_text(encoding="utf-8")
        
        skills = {
            "expertise": [],
            "programming_language": [],
            "technologies": []
        }
        
        # Map des noms de catégories .tex vers nos clés
        category_map = {
            "Expertise": "expertise",
            "Programming Languages": "programming_language",
            "Technologies": "technologies"
        }
        
        # Parse each skill category
        for tex_name, key in category_map.items():
            # Pattern: {\sl Category:} skill1, skill2, skill3\\
            # Use (.+?) to capture everything (including single backslashes like \LaTeX) until \\
            pattern = re.compile(
                rf"\{{\\sl\s*{re.escape(tex_name)}:\}}\s*(.+?)\\\\",
                re.IGNORECASE
            )
            match = pattern.search(resume_content)
            if match:
                skills_text = match.group(1).strip()
                # Split by comma and clean each skill
                skill_list = [s.strip() for s in skills_text.split(",") if s.strip()]
                skills[key] = skill_list
        
        return jsonify(skills)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/apply-manual-skill-ranking", methods=["POST"])
def apply_manual_skill_ranking():
    """Applies a manual ranking of skills to the resume."""
    data = request.get_json()
    skill_ranking = data.get("skill_ranking")
    
    if not skill_ranking or not isinstance(skill_ranking, dict):
        return jsonify({"success": False, "error": "Invalid skill ranking provided"}), 400
    
    try:
        from jobseeker_agent.customizer.agents.ranker import reorder_skills
        
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        resume_content = resume_file.read_text(encoding="utf-8")
        
        # Apply the reordering
        updated_content = reorder_skills(resume_content, skill_ranking)
        resume_file.write_text(updated_content, encoding="utf-8")
        
        # Recompile the PDF
        compile_success, compile_log = compile_utils.compile_tex()
        if not compile_success:
            # Revert the change if compilation fails
            resume_file.write_text(resume_content, encoding="utf-8")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"PDF recompilation failed: {compile_log}",
                    }
                ),
                500,
            )
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/ranking-report")
def get_ranking_report():
    """Serves the ranking report JSON file."""
    report_file = get_data_path() / "resume" / str(state.JOB_ID) / "ranking_report.json"
    try:
        return send_from_directory(report_file.parent, report_file.name)
    except FileNotFoundError:
        return jsonify({"error": "Ranking report file not found"}), 404


@bp.route("/job-description")
def get_job_description():
    """Serves the job description text."""
    if state.JOB_DESCRIPTION:
        return jsonify({"description": state.JOB_DESCRIPTION})
    else:
        return jsonify({"error": "Job description not loaded"}), 404


@bp.route("/job-details")
def get_job_details():
    """Serves the full job details."""
    print(f"Serving job details")
    if state.JOB_DETAILS:
        return jsonify(state.JOB_DETAILS)
    else:
        return jsonify({"error": "Job details not loaded"}), 404


@bp.route("/save-validated-keywords", methods=["POST"])
def save_validated_keywords():
    """Saves the validated keywords to a new JSON file."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    output_file = (
        get_data_path() / "resume" / str(state.JOB_ID) / "keywords_validated.json"
    )
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/keywords")
def get_keywords():
    """Serves the keywords JSON file (validated version if available)."""
    job_dir = get_data_path() / "resume" / str(state.JOB_ID)
    
    # Check for validated keywords first
    validated_file = job_dir / "keywords_validated.json"
    if validated_file.exists():
        try:
            with open(validated_file, "r", encoding="utf-8") as f:
                validated_data = json.load(f)
            return jsonify({"validated": True, "keywords": validated_data})
        except Exception as e:
            print(f"Error loading validated keywords: {e}")
    
    # Fall back to raw keywords
    keywords_file = job_dir / "keywords.json"
    try:
        return send_from_directory(keywords_file.parent, keywords_file.name)
    except FileNotFoundError:
        return jsonify({"error": "Keywords file not found"}), 404


@bp.route("/titles")
def get_titles():
    """Serves the titles JSON file."""
    titles_file = get_data_path() / "resume" / str(state.JOB_ID) / "titles.json"
    try:
        return send_from_directory(titles_file.parent, titles_file.name)
    except FileNotFoundError:
        return jsonify({"error": "Titles file not found"}), 404


@bp.route("/tex")
def serve_tex():
    """Serves the raw TeX file content."""
    tex_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
    try:
        content = tex_file.read_text(encoding="utf-8")
        return jsonify({"content": content})
    except FileNotFoundError:
        return jsonify({"error": "TeX file not found"}), 404


@bp.route("/cover-letter-tex")
def serve_cover_letter_tex():
    """Serves the raw cover-letter.tex file content."""
    tex_file = get_data_path() / "resume" / str(state.JOB_ID) / "cover-letter.tex"
    try:
        content = tex_file.read_text(encoding="utf-8")
        return jsonify({"content": content})
    except FileNotFoundError:
        return jsonify({"error": "Cover letter TeX file not found"}), 404


@bp.route("/pdf/<path:filename>")
def serve_pdf(filename: str):
    """Serves the generated PDF."""
    pdf_directory = get_data_path() / "resume" / str(state.JOB_ID)
    response = send_from_directory(pdf_directory, filename)
    response.headers['Content-Disposition'] = 'inline'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

