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
from . import state, utils, tasks
from jobseeker_agent.utils.paths import (
    get_data_path,
    load_prompt,
    load_cv_template,
    load_reviews,
)

bp = Blueprint(
    "customizer", __name__, template_folder="templates", static_folder="static"
)


@bp.route("/apply/<int:job_id>")
def apply_for_job(job_id: int):
    """Sets the job_id for the customizer interface and renders the dashboard."""
    print(f"--- Customizer: Received request to apply for job_id: {job_id} ---")
    state.JOB_ID = job_id
    print(f"Customizer state JOB_ID set to: {state.JOB_ID}")
    return render_template("customizer_dashboard.html")


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
    return render_template("customizer_dashboard.html")


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
        success, error_log = utils.compile_tex()
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
        success, error_log = utils.compile_tex()
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

        success, error_log = utils.compile_tex()
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

        compile_success, compile_log = utils.compile_tex()
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

            response = tasks.execute_keywords(
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

        compile_success, compile_log = utils.compile_tex()
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
        state.EXTRACTION_THREAD = threading.Thread(target=tasks.run_keyword_extraction_task)
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
        state.DATA_LOADING_THREAD = threading.Thread(target=tasks.run_initial_load_task)
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
        state.RANKING_THREAD = threading.Thread(target=tasks.run_ranker_task)
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
        state.INTRODUCTION_THREAD = threading.Thread(target=tasks.run_introducer_task)
        state.INTRODUCTION_THREAD.daemon = True
        state.INTRODUCTION_THREAD.start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@bp.route("/introduction-status")
def introduction_status():
    """Checks the status of the introduction suggestion."""
    return jsonify(state.INTRODUCTION_STATUS)


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

        compile_success, compile_log = utils.compile_tex()
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
    """Serves the keywords JSON file."""
    keywords_file = get_data_path() / "resume" / str(state.JOB_ID) / "keywords.json"
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


@bp.route("/pdf/<path:filename>")
def serve_pdf(filename: str):
    """Serves the generated PDF."""
    pdf_directory = get_data_path() / "resume" / str(state.JOB_ID)
    return send_from_directory(pdf_directory, filename)
