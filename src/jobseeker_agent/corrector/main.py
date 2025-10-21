import os
import json
from typing import List, Tuple, Any
import subprocess
import webbrowser
import threading

from flask import (
    Flask,
    render_template_string,
    send_from_directory,
    url_for,
    jsonify,
    request,
)

from jobseeker_agent.corrector.experience_corrector import correct_experiences
from jobseeker_agent.corrector.title_corrector import correct_title
from jobseeker_agent.corrector.experience_ranker import rank_experiences
from jobseeker_agent.corrector.skill_ranker import rank_skills
from jobseeker_agent.utils.paths import load_prompt, load_cv_template, get_data_path, load_raw_job
from jobseeker_agent.corrector.keyword_extractor import extract_keywords
from jobseeker_agent.corrector.keyword_inserter import insert_keywords
from jobseeker_agent.corrector.keyword_corrector import correct_keywords
from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job


def save_results(to_save: List[Tuple[str, Any, str]], process_name: str) -> None:
    process_dir = get_data_path() / "resume" / "process" / process_name
    os.makedirs(process_dir, exist_ok=True)
    for name, value, ext in to_save:
        file_path = process_dir / f"{name}.{ext}"
        with open(file_path, "w", encoding="utf-8") as f:
            if ext == "json":
                json.dump(value, f, indent=2, ensure_ascii=False)
            elif ext == "tex":
                f.write(value)
            elif ext == "md":
                f.write(value)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
        print(f"✅ {name} saved to: {file_path}")


app = Flask(__name__)

JOB_ID = 270
JOB_DESCRIPTION = ""


@app.route("/")
def dashboard():
    """Renders the main dashboard HTML."""
    return render_template_string(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Resume Corrector</title>
        <style>
            body, html { height: 100%; margin: 0; font-family: sans-serif; }
            .container { display: flex; height: 100%; }
            .left-pane { flex: 1; padding: 1em; border-right: 1px solid #ddd; overflow-y: auto; }
            .right-pane { flex: 1; display: flex; flex-direction: column; }
            .toolbar { padding: 10px; border-bottom: 1px solid #ddd; background-color: #f8f8f8; flex-shrink: 0; display: flex; align-items: center; }
            .content-view { flex-grow: 1; }
            embed { width: 100%; height: 100%; border: none; }
            #tex-viewer { height: 100%; }
            #tex-editor { width: 100%; height: 100%; border: none; resize: none; font-family: monospace; padding: 1em; box-sizing: border-box; }
            #job-viewer { height: 100%; overflow-y: auto; }
            #job-viewer pre { white-space: pre-wrap; word-wrap: break-word; padding: 1em; margin: 0; }
            h1 { color: #2c3e50; }
            .toolbar-btn {
                background-color: #ecf0f1;
                color: #34495e;
                border: 1px solid #bdc3c7;
                padding: 8px 12px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.9em;
                margin-right: 10px;
                transition: background-color 0.2s, color 0.2s;
            }
            .toolbar-btn:hover {
                background-color: #dce4e7;
            }
            .toolbar-btn.action-btn {
                background-color: #3498db;
                color: white;
                border-color: #3498db;
            }
            .toolbar-btn.action-btn:hover {
                 background-color: #2980b9;
            }
            .toolbar-btn.active {
                background-color: #95a5a6;
                color: white;
                border-color: #7f8c8d;
            }
            .view-switcher {
                margin-left: auto;
            }
            #save-btn {
                background-color: #27ae60;
                border-color: #27ae60;
            }
            #save-btn:hover {
                background-color: #229954;
            }

            /* Keyword styles */
            #keywords-container {
                margin-top: 1.5em;
                display: flex;
                flex-wrap: wrap;
                gap: 1.5em;
            }
            .keyword-group {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 1em;
                position: relative;
                transition: background-color 0.3s ease;
                flex: 1 1 calc(50% - 2em - 0.75em); /* 50% width minus padding and gap */
                box-sizing: border-box;
            }
            .keyword-group.validated {
                background-color: #eafaf1;
                border-color: #27ae60;
            }
            .keyword-group h3 {
                margin: 0 0 1em 0;
                font-size: 1.1em;
                color: #34495e;
            }
            .keyword-subgroup {
                margin-bottom: 1em;
            }
            .keyword-subgroup:last-child {
                margin-bottom: 0;
            }
            .keyword-subgroup h4 {
                margin: 0 0 0.5em 0;
                font-size: 0.95em;
                color: #555;
                font-weight: 600;
                text-transform: capitalize;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.3em;
            }
            .keyword-labels {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            .keyword-label {
                background-color: #ecf0f1;
                color: #34495e;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 0.9em;
                display: flex;
                align-items: center;
                position: relative;
            }
            .keyword-label.match-present {
                background-color: #27ae60;
                color: white;
            }
            .keyword-label.match-absent {
                background-color: #f39c12;
                color: white;
            }
            .keyword-label.mismatch-absent {
                background-color: #c0392b;
                color: white;
            }
            .remove-btn {
                cursor: pointer;
                font-weight: bold;
                color: #c0392b;
                background: none;
                border: none;
                font-size: 1.2em;
                line-height: 1;
            }
            .keyword-label .remove-btn {
                margin-left: 8px;
                font-size: 1em;
                visibility: hidden;
                opacity: 0;
                transition: opacity 0.2s ease;
            }
            .keyword-label.match-present .remove-btn,
            .keyword-label.match-absent .remove-btn,
            .keyword-label.mismatch-absent .remove-btn {
                color: white;
            }
            .keyword-label:hover .remove-btn {
                visibility: visible;
                opacity: 1;
            }
            .group-remove-btn {
                position: absolute;
                top: 10px;
                right: 10px;
            }
            .input-area {
                margin-top: 1em;
                display: flex;
                gap: 10px;
            }
            .input-area input {
                flex-grow: 1;
                border: 1px solid #ccc;
                padding: 8px;
                border-radius: 5px;
            }
            .validate-btn {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 0 15px;
                border-radius: 5px;
                cursor: pointer;
            }
            .validate-btn:hover {
                background-color: #27ae60;
            }

            #finalize-btn {
                width: 100%;
                padding: 12px;
                font-size: 1.1em;
                background-color: #16a085;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 1em;
            }
            #finalize-btn:hover {
                background-color: #117a65;
            }
            #finalize-btn:disabled {
                background-color: #bdc3c7;
                cursor: not-allowed;
            }

        </style>
    </head>
    <body>
        <div class="container">
            <div class="left-pane">
                <h1>Workspace</h1>
                <div id="keywords-container"></div>
                <button id="finalize-btn" disabled>Finalize & Save Keywords</button>
            </div>
            <div class="right-pane">
                <div class="toolbar">
                    <button id="refresh-btn" class="toolbar-btn action-btn">Refresh</button>
                    <button id="save-btn" class="toolbar-btn action-btn" style="display: none;">Save</button>
                    <div class="view-switcher">
                        <button id="view-pdf-btn" class="toolbar-btn active">PDF</button>
                        <button id="view-tex-btn" class="toolbar-btn">TeX</button>
                        <button id="view-job-btn" class="toolbar-btn">Job</button>
                    </div>
                </div>
                <div class="content-view" style="color-scheme: light;">
                    <embed id="pdf-viewer" src="{{ url_for('serve_pdf', filename='resume.pdf') }}#toolbar=0" type="application/pdf" />
                    <div id="tex-viewer" style="display: none;">
                        <textarea id="tex-editor"></textarea>
                    </div>
                    <div id="job-viewer" style="display: none;">
                        <pre id="job-content"></pre>
                    </div>
                </div>
            </div>
        </div>
        <script>
            const refreshBtn = document.getElementById('refresh-btn');
            const saveBtn = document.getElementById('save-btn');
            const pdfViewer = document.getElementById('pdf-viewer');
            const texViewer = document.getElementById('tex-viewer');
            const jobViewer = document.getElementById('job-viewer');
            const texEditor = document.getElementById('tex-editor');
            const jobContent = document.getElementById('job-content');
            const viewPdfBtn = document.getElementById('view-pdf-btn');
            const viewTexBtn = document.getElementById('view-tex-btn');
            const viewJobBtn = document.getElementById('view-job-btn');

            function refreshPdf() {
                if (pdfViewer) {
                    const url = new URL(pdfViewer.src);
                    url.searchParams.set('t', new Date().getTime());
                    pdfViewer.src = url.href;
                }
            }

            function refreshTex() {
                fetch("{{ url_for('serve_tex') }}")
                    .then(response => response.json())
                    .then(data => {
                        if (data.content) {
                            texEditor.value = data.content;
                        } else {
                            texEditor.value = "Error loading TeX file: " + (data.error || "Unknown error");
                        }
                    });
            }

            function fetchJobDescription() {
                 fetch("{{ url_for('get_job_description') }}")
                    .then(response => response.json())
                    .then(data => {
                        if (data.description) {
                            jobContent.textContent = data.description;
                        } else {
                            jobContent.textContent = "Error loading job description: " + (data.error || "Unknown error");
                        }
                    });
            }

            refreshBtn.addEventListener('click', refreshPdf);
            
            viewPdfBtn.addEventListener('click', function() {
                pdfViewer.style.display = 'block';
                texViewer.style.display = 'none';
                jobViewer.style.display = 'none';
                refreshBtn.style.display = 'inline-block';
                saveBtn.style.display = 'none';
                viewPdfBtn.classList.add('active');
                viewTexBtn.classList.remove('active');
                viewJobBtn.classList.remove('active');
            });

            viewTexBtn.addEventListener('click', function() {
                pdfViewer.style.display = 'none';
                texViewer.style.display = 'block';
                jobViewer.style.display = 'none';
                refreshBtn.style.display = 'none';
                saveBtn.style.display = 'inline-block';
                viewPdfBtn.classList.remove('active');
                viewTexBtn.classList.add('active');
                viewJobBtn.classList.remove('active');
                if (!texEditor.value) {
                    refreshTex();
                }
            });

            viewJobBtn.addEventListener('click', function() {
                pdfViewer.style.display = 'none';
                texViewer.style.display = 'none';
                jobViewer.style.display = 'block';
                refreshBtn.style.display = 'none';
                saveBtn.style.display = 'none';
                viewPdfBtn.classList.remove('active');
                viewTexBtn.classList.remove('active');
                viewJobBtn.classList.add('active');
                if (!jobContent.textContent) {
                    fetchJobDescription();
                }
            });

            function checkValidationState() {
                const finalizeBtn = document.getElementById('finalize-btn');
                const groups = document.querySelectorAll('.keyword-group');
                if (groups.length === 0) {
                    finalizeBtn.disabled = true;
                    return;
                }
                const allValidated = Array.from(groups).every(group => group.classList.contains('validated'));
                finalizeBtn.disabled = !allValidated;
            }

            document.addEventListener('DOMContentLoaded', function() {
                fetch("{{ url_for('get_keywords') }}")
                    .then(response => response.json())
                    .then(data => {
                        const container = document.getElementById('keywords-container');
                        if (!container || data.error) {
                            console.error("Error loading keywords:", data.error);
                            return;
                        }

                        for (const groupTitle in data) {
                            const groupData = data[groupTitle];
                            const groupDiv = document.createElement('div');
                            groupDiv.className = 'keyword-group';

                            const title = document.createElement('h3');
                            title.textContent = groupTitle;
                            groupDiv.appendChild(title);

                            const groupRemoveBtn = document.createElement('button');
                            groupRemoveBtn.className = 'remove-btn group-remove-btn';
                            groupRemoveBtn.innerHTML = '&times;';
                            groupRemoveBtn.onclick = () => {
                                groupDiv.remove();
                                checkValidationState();
                            };
                            groupDiv.appendChild(groupRemoveBtn);

                            for (const subGroupTitle in groupData) {
                                const keywords = groupData[subGroupTitle];
                                if (!Array.isArray(keywords) || keywords.length === 0) continue;

                                const subGroupDiv = document.createElement('div');
                                subGroupDiv.className = 'keyword-subgroup';

                                const subTitle = document.createElement('h4');
                                subTitle.textContent = subGroupTitle.replace(/_/g, ' ');
                                subGroupDiv.appendChild(subTitle);

                                const labelsDiv = document.createElement('div');
                                labelsDiv.className = 'keyword-labels';
                                keywords.forEach(keyword => {
                                    const labelSpan = document.createElement('span');
                                    labelSpan.className = 'keyword-label';
                                    labelSpan.classList.add(subGroupTitle.replace(/_/g, '-'));

                                    labelSpan.textContent = keyword;

                                    const labelRemoveBtn = document.createElement('button');
                                    labelRemoveBtn.className = 'remove-btn';
                                    labelRemoveBtn.innerHTML = '&times;';
                                    labelRemoveBtn.onclick = () => labelSpan.remove();
                                    labelSpan.appendChild(labelRemoveBtn);

                                    labelsDiv.appendChild(labelSpan);
                                });
                                subGroupDiv.appendChild(labelsDiv);
                                groupDiv.appendChild(subGroupDiv);
                            }

                            const inputArea = document.createElement('div');
                            inputArea.className = 'input-area';
                            const input = document.createElement('input');
                            input.type = 'text';
                            input.placeholder = 'Add a note...';
                            const validateBtn = document.createElement('button');
                            validateBtn.className = 'validate-btn';
                            validateBtn.textContent = '✓';
                            validateBtn.onclick = () => {
                                groupDiv.classList.toggle('validated');
                                checkValidationState();
                            };
                            inputArea.appendChild(input);
                            inputArea.appendChild(validateBtn);
                            groupDiv.appendChild(inputArea);

                            container.appendChild(groupDiv);
                        }
                    });
            });

            document.getElementById('finalize-btn').addEventListener('click', function() {
                const finalData = {};
                document.querySelectorAll('.keyword-group').forEach(groupDiv => {
                    const title = groupDiv.querySelector('h3').textContent;
                    const keywords = Array.from(groupDiv.querySelectorAll('.keyword-label')).map(label => {
                        // Clone node to not include the remove button's text content
                        const clone = label.cloneNode(true);
                        clone.querySelector('.remove-btn').remove();
                        return clone.textContent.trim();
                    });
                    const instructions = groupDiv.querySelector('input').value;

                    finalData[title] = {
                        keywords: keywords,
                        instructions: instructions
                    };
                });

                const btn = this;
                btn.textContent = 'Saving...';
                btn.disabled = true;

                fetch("{{ url_for('save_validated_keywords') }}", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(finalData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Validated keywords saved successfully!');
                    } else {
                        alert('Error saving keywords: ' + (data.error || 'Unknown error'));
                    }
                })
                .finally(() => {
                    btn.textContent = 'Finalize & Save Keywords';
                    checkValidationState(); // Re-check state, might need to disable
                });
            });


            saveBtn.addEventListener('click', function() {
                const content = texEditor.value;
                saveBtn.textContent = 'Saving...';
                saveBtn.disabled = true;
                fetch("{{ url_for('save_tex') }}", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: content })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('File saved and recompiled successfully!');
                        // Switch to PDF view and refresh to see changes
                        viewPdfBtn.click();
                        refreshPdf();
                    } else {
                        alert('Error saving file: ' + (data.error || 'Unknown error'));
                    }
                })
                .finally(() => {
                    saveBtn.textContent = 'Save';
                    saveBtn.disabled = false;
                });
            });
        </script>
    </body>
    </html>
    """
    )


def compile_tex():
    """Compiles the TeX file to a PDF."""
    job_dir = get_data_path() / "resume" / f"{JOB_ID}"
    print(f"Compiling resume.tex for job {JOB_ID}...")
    result = subprocess.run(
        ["pdflatex", "-output-directory", str(job_dir), str(job_dir / "resume.tex")],
        capture_output=True,
        text=True,
    )
    print("Compilation finished.")
    if result.returncode != 0:
        print("--- LaTeX Compilation Error ---")
        print(result.stdout)
        print(result.stderr)
        return False, result.stdout
    return True, ""


@app.route("/save-tex", methods=["POST"])
def save_tex():
    """Saves the edited TeX content and recompiles."""
    data = request.get_json()
    content = data.get("content")
    if content is None:
        return jsonify({"success": False, "error": "No content provided"}), 400

    tex_file = get_data_path() / "resume" / str(JOB_ID) / "resume.tex"
    try:
        tex_file.write_text(content, encoding="utf-8")
        success, error_log = compile_tex()
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": f"Compilation failed:\n{error_log}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/job-description")
def get_job_description():
    """Serves the job description text."""
    if JOB_DESCRIPTION:
        return jsonify({"description": JOB_DESCRIPTION})
    else:
        return jsonify({"error": "Job description not loaded"}), 404


@app.route("/save-validated-keywords", methods=["POST"])
def save_validated_keywords():
    """Saves the validated keywords to a new JSON file."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    output_file = get_data_path() / "resume" / str(JOB_ID) / "keywords_validated.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/keywords")
def get_keywords():
    """Serves the keywords JSON file."""
    keywords_file = get_data_path() / "resume" / str(JOB_ID) / "keywords.json"
    try:
        return send_from_directory(keywords_file.parent, keywords_file.name)
    except FileNotFoundError:
        return jsonify({"error": "Keywords file not found"}), 404


@app.route("/tex")
def serve_tex():
    """Serves the raw TeX file content."""
    tex_file = get_data_path() / "resume" / str(JOB_ID) / "resume.tex"
    try:
        content = tex_file.read_text(encoding="utf-8")
        return jsonify({"content": content})
    except FileNotFoundError:
        return jsonify({"error": "TeX file not found"}), 404


@app.route("/pdf/<path:filename>")
def serve_pdf(filename: str):
    """Serves the generated PDF."""
    pdf_directory = get_data_path() / "resume" / str(JOB_ID)
    return send_from_directory(pdf_directory, filename)


def main():
    """Main function to prepare resume and run the Flask app."""
    # --- Resume Preparation ---
    global JOB_DESCRIPTION
    model = "gpt-5-mini"
    job = load_raw_job(JOB_ID)
    job_details = analyze_linkedin_job(job["job_link"])
    JOB_DESCRIPTION = job_details.get("description", "Could not fetch job description.")
    profil_pro = load_prompt("profil_pro")
    resume = load_cv_template()
    # create a new directory for the job
    job_dir = get_data_path() / "resume" / f"{JOB_ID}"
    os.makedirs(job_dir, exist_ok=True)
    # save the tex template in the job directory
    with open(job_dir / "resume.tex", "w", encoding="utf-8") as f:
        f.write(resume)
    # compile the tex template
    compile_tex()

    # --- Old logic from main.py ---
    # print(job["job_link"])

    # response = rank_experiences(job_description, profil_pro, resume, model)
    # print(response["ranking"])
    # resume = response["resume"]
    # to_save = [("ranking", response["ranking"], "json"), ("resume", resume, "tex")]
    # save_results(to_save, "1_ranked_experiences")

    # keywords = extract_keywords(job_details, profil_pro, resume, model)
    # import json
    # print(json.dumps(keywords, indent=2, ensure_ascii=False))
    # to_save = [("keywords", keywords, "json")]
    # save_results(to_save, "2_extracted_keywords")

    # response = insert_keywords(
    #     job_description,
    #     profil_pro,
    #     resume,
    #     keywords_present=keywords["match_present"],
    #     keywords_absent=keywords["match_absent"],
    #     model=model
    # )
    # print(*response["report"], sep="\n")
    # resume = response["resume"]
    # keywords["match_present"] = response["keywords_present"]
    # to_save = [("keywords", keywords, "json"), ("resume", resume, "tex"), ("report", response["report"], "json")]
    # save_results(to_save, "3_inserted_keywords")

    # response = correct_keywords(job_description, profil_pro, resume, keywords["match_present"], keywords["mismatch_absent"], model)
    # if response["any_correction"]:
    #     print(*[json.dumps(r, indent=2, ensure_ascii=False) for r in response["report"]], sep="\n")
    #     resume = response["resume"]
    #     print(response.keys())
    #     keywords["match_present"] = response["keywords_present"]
    # to_save = [("keywords", keywords, "json"), ("resume", resume, "tex"), ("report", response["report"], "json")]
    # save_results(to_save, "4_corrected_keywords")

    # response = rank_skills(job_description, profil_pro, resume, model)
    # resume = response["resume"]
    # to_save = [("resume", resume, "tex")]
    # save_results(to_save, "5_ranked_skills")

    # response = correct_title(job_description, profil_pro, resume, model)
    # print(response["title"])
    # resume = response["resume"]
    # to_save = [("resume", resume, "tex"), ("title", response["title"], "md")]
    # save_results(to_save, "6_corrected_title")

    # # response = correct_experiences(job_description, profil_pro, resume, model)
    # # if response["any_correction"]:
    # #     print(response["report"])
    # #     resume = response["resume"]

    # file_path = get_data_path() / "resume" / "test" / f"cv-test.tex"
    # try:
    #     with open(file_path, "w", encoding="utf-8") as f:
    #         f.write(resume)
    #     print(f"✅ Le fichier '{file_path}' a été créé avec succès !")
    #     print("Ouvrez-le avec votre éditeur de texte, il sera correctement formaté.")
    # except Exception as e:
    #     print(f"❌ Une erreur est survenue : {e}")

    # --- Run Flask App ---
    url = "http://127.0.0.1:5001/"
    threading.Timer(1.25, lambda: webbrowser.open(url)).start()
    print(f"Starting the dashboard server at {url}")
    print("Press CTRL+C to stop the server.")
    app.run(port=5001, debug=False)


if __name__ == "__main__":
    main()