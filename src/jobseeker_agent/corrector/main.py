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
from jobseeker_agent.corrector.keyword_executor import execute_keywords
from jobseeker_agent.corrector.keyword_extractor_2 import extract_keywords


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
JOB_DETAILS = {}
EXTRACTION_THREAD = None
EXTRACTION_STATUS = {"status": "idle", "error": None}
DATA_LOADING_THREAD = None
DATA_LOADING_STATUS = {"status": "idle", "error": None}


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
            .toolbar { padding: 10px; border-bottom: 1px solid #ddd; background-color: #f8f8f8; flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; }
            .toolbar-center { flex-grow: 1; text-align: center; }
            .content-view { flex-grow: 1; }
            embed { width: 100%; height: 100%; border: none; }
            #tex-viewer { height: 100%; }
            #tex-editor { width: 100%; height: 100%; border: none; resize: none; font-family: monospace; padding: 1em; box-sizing: border-box; }
            #job-viewer { height: 100%; overflow-y: auto; }
            #job-viewer pre { white-space: pre-wrap; word-wrap: break-word; padding: 1em; margin: 0; }
            h1 { color: #2c3e50; }
            .info { background-color: #eaf2f8; border-left: 5px solid #3498db; padding: 1em; margin-bottom: 1em; border-radius: 5px; }
            .job-header h1, .job-header h2 { margin: 0 0 0.25em 0; }
            .job-header h2 { font-weight: normal; color: #555; }
            #job-viewer h3 { border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 1.5em;}
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

            /* Tab styles */
            .tabs {
                display: flex;
                border-bottom: 1px solid #ddd;
                margin-bottom: 1em;
                background-color: #f8f8f8;
                padding: 5px 10px;
                border-radius: 5px;
                overflow-x: auto; /* Allow horizontal scrolling for many tabs */
            }
            .tab-btn {
                background-color: #ecf0f1;
                color: #34495e;
                border: 1px solid #bdc3c7;
                padding: 8px 15px;
                border-radius: 5px 5px 0 0;
                cursor: pointer;
                font-size: 0.9em;
                margin-right: 5px;
                transition: background-color 0.2s, color 0.2s;
                white-space: nowrap; /* Prevent text wrapping */
            }
            .tab-btn:hover {
                background-color: #dce4e7;
            }
            .tab-btn.active {
                background-color: #3498db;
                color: white;
                border-color: #3498db;
            }
            .tab-content {
                display: none; /* Hidden by default */
                padding: 1em;
                border: 1px solid #ddd;
                border-top: none;
                border-radius: 0 5px 5px 5px;
                background-color: #f8f8f8;
                overflow-y: auto; /* Allow scrolling for long content */
            }
            .tab-content.active {
                display: block; /* Show the active tab */
            }

            /* Title suggestions styles */
            #title-suggestions-container {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 1em;
                margin-bottom: 1.5em;
            }
            #title-suggestions-container h4 {
                margin: 0 0 0.75em 0;
                color: #495057;
            }
            #title-suggestions-list {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin: 0;
                padding: 0;
            }
            .title-suggestion-btn {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                padding: 8px 12px;
                border-radius: 20px;
                cursor: pointer;
                transition: background-color 0.2s, border-color 0.2s;
            }
            .title-suggestion-btn:hover {
                background-color: #dee2e6;
            }
            .title-suggestion-btn.selected {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
            }
            #custom-title-area {
                margin-top: 1em;
                display: flex;
                gap: 10px;
            }
            #custom-title-input {
                flex-grow: 1;
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 8px;
            }

        </style>
    </head>
    <body>
        <div class="container">
            <div class="left-pane">
                <h1>Workspace</h1>
                <div id="initial-loading-container">
                    <h4>Loading Job Data...</h4>
                    <p>This may take a moment. The interface will appear here once the process is complete.</p>
                </div>
                <div id="main-content" style="display: none;">
                    <div class="tabs">
                        <button class="tab-btn active" data-tab="keywords">Keywords</button>
                        <button class="tab-btn" data-tab="executor">Executor</button>
                    </div>
                    <div id="keywords-tab" class="tab-content" style="display: block;">
                        <div id="keyword-loading-container">
                            <h4>Extracting Keywords & Titles...</h4>
                            <p>This may take a moment. The interface will appear here once the process is complete.</p>
                        </div>
                        <div id="data-container" style="display: none;">
                            <div id="title-suggestions-container" style="display: none;">
                                <h4>Title Suggestions</h4>
                                <div id="title-suggestions-list"></div>
                                <div id="custom-title-area">
                                    <input type="text" id="custom-title-input" placeholder="Enter a custom title...">
                                    <button id="apply-custom-title-btn" class="toolbar-btn action-btn">Apply</button>
                                </div>
                            </div>
                            <div id="keywords-container"></div>
                            <button id="finalize-btn" disabled>Finalize & Save Keywords</button>
                        </div>
                    </div>
                    <div id="executor-tab" class="tab-content" style="display: none;">
                        <button id="run-executor-btn" class="toolbar-btn action-btn" style="width: 100%; margin-bottom: 1em;">Run Keyword Executor</button>
                        <h4>Execution Report:</h4>
                        <pre id="executor-report" style="background-color: #f8f8f8; border: 1px solid #ddd; padding: 1em; border-radius: 5px; min-height: 200px;"></pre>
                    </div>
                </div>
            </div>
            <div class="right-pane">
                <div class="toolbar">
                    <div class="toolbar-left">
                        <button id="refresh-btn" class="toolbar-btn action-btn">Refresh</button>
                        <button id="save-btn" class="toolbar-btn action-btn" style="display: none;">Save</button>
                    </div>
                    <div class="toolbar-center">
                    </div>
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
                    <div id="job-viewer" style="display: none; padding: 1em;">
                        <!-- Content will be injected by JS -->
                    </div>
                </div>
            </div>
        </div>
        <script>
            const saveBtn = document.getElementById('save-btn');
            const refreshBtn = document.getElementById('refresh-btn');
            const pdfViewer = document.getElementById('pdf-viewer');
            const texViewer = document.getElementById('tex-viewer');
            const jobViewer = document.getElementById('job-viewer');
            const texEditor = document.getElementById('tex-editor');
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

            function fetchJobDetails() {
                fetch("{{ url_for('get_job_details') }}")
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('job-viewer');
                    if (data.error) {
                        container.innerHTML = `<p>Error loading job details: ${data.error}</p>`;
                        return;
                    }

                    const score = data.score !== null && data.score !== undefined ? `(${data.score})` : '';

                    container.innerHTML = `
                        <div class="job-header">
                            <h1>${ data.title || 'N/A' }</h1>
                            <h2>${ data.company_name || 'N/A' } - ${ data.location || 'N/A' }</h2>
                            <p>Posted: ${ data.posted_date || 'N/A' } | Workplace: ${ data.workplace_type || 'N/A' }</p>
                        </div>
                        <hr>
                        <h3>Full Job Description</h3>
                        <pre>${ data.description || 'Not available.' }</pre>
                        <h3>Synthesis and Decision</h3>
                        <pre>${ data.synthesis || 'Not available.' }</pre>
                        <h3>Evaluation Grid ${score}</h3>
                        <pre>${ data.evaluation_grid || 'Not available.' }</pre>
                    `;
                });
            }

            refreshBtn.addEventListener('click', () => {
                // If in TeX view, recompile. If in PDF view, just refresh.
                if (texViewer.style.display === 'block') {
                    fetch("{{ url_for('recompile_tex') }}", { method: 'POST' })
                        .then(res => res.json())
                        .then(data => {
                            if(data.success) {
                                alert('Recompilation successful!');
                                setTimeout(() => {
                                    refreshPdf();
                                }, 1500); // Wait 1.5 seconds for compilation
                            } else {
                                alert('Recompilation failed: ' + data.error);
                            }
                        });
                } else {
                    refreshPdf();
                }
            });
            
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
                refreshBtn.style.display = 'inline-block';
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
                if (jobViewer.children.length === 0) {
                    fetchJobDetails();
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

            function startAndPollExtraction() {
                function pollExtractionStatus() {
                    fetch("{{ url_for('extraction_status') }}")
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'complete') {
                            const keywordsPromise = fetch("{{ url_for('get_keywords') }}").then(res => res.json());
                            const titlesPromise = fetch("{{ url_for('get_titles') }}").then(res => res.json());
                            Promise.all([keywordsPromise, titlesPromise])
                                .then(([keywordsData, titlesData]) => {
                                    renderData(keywordsData, titlesData);
                                })
                                .catch(error => console.error("Failed to fetch final data:", error));
                        } else if (data.status === 'pending') {
                            setTimeout(pollExtractionStatus, 2000);
                        } else if (data.status === 'failed') {
                            const loader = document.getElementById('keyword-loading-container');
                            loader.innerHTML = `<h4>Extraction Failed</h4><p>${data.error || 'An unknown error occurred.'}</p>`;
                        }
                    });
                }

                fetch("{{ url_for('start_extraction') }}", { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started' || data.status === 'complete') {
                        pollExtractionStatus();
                    } else {
                         const loader = document.getElementById('keyword-loading-container');
                         loader.innerHTML = `<h4>Could not start extraction</h4><p>${data.error || 'An unknown error occurred.'}</p>`;
                    }
                });
            }

            function renderData(keywordsData, titlesData) {
                document.getElementById('keyword-loading-container').style.display = 'none';
                document.getElementById('data-container').style.display = 'block';

                const titlesContainer = document.getElementById('title-suggestions-container');
                const titlesList = document.getElementById('title-suggestions-list');
                if (titlesList && Array.isArray(titlesData) && titlesData.length > 0) {
                    titlesData.forEach(title => {
                        const btn = document.createElement('button');
                        btn.className = 'title-suggestion-btn';
                        btn.textContent = title;
                        btn.onclick = () => updateTitle(title, btn);
                        titlesList.appendChild(btn);
                    });
                    titlesContainer.style.display = 'block';
                } else {
                    console.error("No titles found or error loading titles:", titlesData);
                }

                const container = document.getElementById('keywords-container');
                if (!container || keywordsData.error) {
                    console.error("Error loading keywords:", keywordsData.error);
                    return;
                }
                container.innerHTML = '';
                for (const groupTitle in keywordsData) {
                    const groupData = keywordsData[groupTitle];
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
            }

            function updateTitle(title, clickedButton = null) {
                document.querySelectorAll('.title-suggestion-btn').forEach(b => b.classList.remove('selected'));
                if (clickedButton) {
                    clickedButton.classList.add('selected');
                }
                fetch("{{ url_for('update_title') }}", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: title })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Title updated successfully.');
                        document.getElementById('tex-editor').value = "";
                        refreshTex();
                        setTimeout(() => {
                            refreshPdf();
                            document.getElementById('view-pdf-btn').click();
                        }, 1500);
                    } else {
                        alert('Error updating title: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Failed to update title:', error);
                    alert('An error occurred while updating the title.');
                });
            }

            // --- Main script execution ---
            document.addEventListener('DOMContentLoaded', function() {
                console.log("DOMContentLoaded event fired.");

                // Element Declarations
                console.log("Elements declared:", { saveBtn, refreshBtn, viewPdfBtn });

                // Initial Load
                function pollInitialLoadStatus() {
                    fetch("{{ url_for('initial_load_status') }}")
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'complete') {
                            document.getElementById('initial-loading-container').style.display = 'none';
                            document.getElementById('main-content').style.display = 'block';
                            // Now that initial data is loaded, start the keyword extraction
                            startAndPollExtraction();
                        } else if (data.status === 'pending') {
                            setTimeout(pollInitialLoadStatus, 2000); // Poll again
                        } else if (data.status === 'failed') {
                            const loader = document.getElementById('initial-loading-container');
                            loader.innerHTML = `<h4>Failed to load job data</h4><p>${data.error || 'An unknown error occurred.'}</p>`;
                        }
                    });
                }

                console.log("Starting initial data load fetch...");
                fetch("{{ url_for('start_initial_load') }}", { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started' || data.status === 'complete' || data.status === 'already_running') {
                        pollInitialLoadStatus();
                    } else {
                        const loader = document.getElementById('initial-loading-container');
                        loader.innerHTML = `<h4>Could not start data loading</h4><p>${data.error || 'An unknown error occurred.'}</p>`;
                    }
                });

                // Custom title button event
                document.getElementById('apply-custom-title-btn').addEventListener('click', () => {
                    const input = document.getElementById('custom-title-input');
                    const customTitle = input.value.trim();
                    if (customTitle) {
                        updateTitle(customTitle);
                    } else {
                        alert('Please enter a custom title.');
                    }
                });

                // Tab switching logic
                document.querySelectorAll('.tab-btn').forEach(button => {
                    button.addEventListener('click', () => {
                        const tabId = button.dataset.tab;
                        document.querySelectorAll('.tab-content').forEach(tab => {
                            tab.style.display = tab.id === `${tabId}-tab` ? 'block' : 'none';
                        });
                        document.querySelectorAll('.tab-btn').forEach(btn => {
                            btn.classList.remove('active');
                        });
                        button.classList.add('active');
                    });
                });

                // Executor logic
                document.getElementById('run-executor-btn').addEventListener('click', function() {
                    const btn = this;
                    const reportPre = document.getElementById('executor-report');
                    btn.textContent = 'Executing...';
                    btn.disabled = true;
                    reportPre.textContent = 'Running... please wait.';

                    fetch("{{ url_for('run_executor') }}", { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            reportPre.textContent = data.report.join('\\n');
                            alert('Execution successful! PDF is being updated.');
                            refreshPdf(); // Refresh the PDF to show changes
                            viewPdfBtn.click(); // Switch to PDF view
                        } else {
                            reportPre.textContent = "Error during execution:\\n" + data.error;
                            alert('Execution failed: ' + (data.error || 'Unknown error'));
                        }
                    })
                    .finally(() => {
                        btn.textContent = 'Run Keyword Executor';
                        btn.disabled = false;
                    });
                });

                document.getElementById('finalize-btn').addEventListener('click', function() {
                    const finalData = {};
                    document.querySelectorAll('.keyword-group').forEach(groupDiv => {
                        const title = groupDiv.querySelector('h3').textContent;
                        const keywords = Array.from(groupDiv.querySelectorAll('.keyword-label')).map(label => {
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
                        checkValidationState();
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
                            texEditor.value = "";
                            setTimeout(() => {
                                viewPdfBtn.click();
                                refreshPdf();
                            }, 1500);
                        } else {
                            alert('Error saving file: ' + (data.error || 'Unknown error'));
                        }
                    })
                    .finally(() => {
                        saveBtn.textContent = 'Save';
                        saveBtn.disabled = false;
                    });
                });
            });
        </script>
    </body>
    </html>
    """
    )


@app.route('/favicon.ico')
def favicon():
    return '', 204


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


@app.route("/recompile-tex", methods=["POST"])
def recompile_tex():
    """Just recompiles the existing TeX file."""
    try:
        success, error_log = compile_tex()
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": f"Compilation failed:\n{error_log}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/update-title", methods=["POST"])
def update_title():
    """Finds and replaces the title in the resume.tex file."""
    data = request.get_json()
    new_title = data.get("title")
    if not new_title:
        return jsonify({"success": False, "error": "No title provided"}), 400

    try:
        resume_file = get_data_path() / "resume" / str(JOB_ID) / "resume.tex"
        content = resume_file.read_text(encoding="utf-8")

        # Use regex to replace the content of \textbf{\LARGE ...}
        import re
        new_content, count = re.subn(r'(\\textbf{\\LARGE )(.*?)(\})', r'\\textbf{\\LARGE ' + new_title + r'}', content, count=1)

        if count == 0:
            return jsonify({"success": False, "error": "\\textbf{\\LARGE ...} tag not found in resume.tex"}), 404
        resume_file.write_text(new_content, encoding="utf-8")

        compile_success, compile_log = compile_tex()
        if not compile_success:
            # Revert the file if compilation fails
            resume_file.write_text(content, encoding="utf-8")
            return jsonify({"success": False, "error": f"PDF recompilation failed: {compile_log}"}), 500

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/run-executor", methods=["POST"])
def run_executor():
    """Runs the keyword executor script."""
    try:
        # 1. Load instructions
        keywords_file = get_data_path() / "resume" / str(JOB_ID) / "keywords_validated.json"
        with open(keywords_file, "r", encoding="utf-8") as f:
            instructions = json.load(f)

        # 2. Load current resume
        resume_file = get_data_path() / "resume" / str(JOB_ID) / "resume.tex"
        resume_content = resume_file.read_text(encoding="utf-8")

        # 3. Load other necessary data
        profil_pro = load_prompt("profil_pro")
        model = "gpt-5-mini" # Or get from request if needed

        # 4. Execute the script
        response = execute_keywords(JOB_DESCRIPTION, profil_pro, resume_content, instructions, model=model)
        new_resume = response["resume"]
        report = response["report"]
        job_dir = get_data_path() / "resume" / str(JOB_ID)
        output_path = job_dir / "insertion_report.json"
        # Save the report to a JSON file for debugging
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        # 5. Overwrite the resume file
        resume_file.write_text(new_resume, encoding="utf-8")

        # 6. Recompile the PDF
        compile_success, compile_log = compile_tex()
        if not compile_success:
            raise Exception(f"PDF recompilation failed: {compile_log}")

        return jsonify({"success": True, "report": report})

    except FileNotFoundError:
        return jsonify({"success": False, "error": "keywords_validated.json not found. Please finalize keywords first."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def run_keyword_extraction_task():
    """The actual keyword extraction logic to be run in a background thread."""
    global EXTRACTION_STATUS
    try:
        print("➡️ [THREAD] Keyword extraction task started.")
        EXTRACTION_STATUS['status'] = 'pending'
        
        # This data needs to be loaded inside the thread
        print("    [THREAD] Loading job, prompt, and resume...")
        job = load_raw_job(JOB_ID)
        profil_pro = load_prompt("profil_pro")
        resume = load_cv_template()
        print("    [THREAD] ...data loaded.")

        print("    [THREAD] Analyzing LinkedIn job page...")
        job_details = analyze_linkedin_job(job["job_link"]) # Assuming this is thread-safe
        if not job_details:
            raise Exception("Failed to analyze LinkedIn job page.")
        print("    [THREAD] ...LinkedIn page analyzed.")

        print("    [THREAD] Calling LLM to extract keywords...")
        extraction_response = extract_keywords(job_details, profil_pro, resume, model="gpt-5-mini")
        print("    [THREAD] ...LLM response received.")

        # Save title suggestions
        titles_file = get_data_path() / "resume" / str(JOB_ID) / "titles.json"
        with open(titles_file, "w", encoding="utf-8") as f:
            json.dump(extraction_response['title_suggestions'], f, indent=4)

        # Save classified keywords
        keywords_file = get_data_path() / "resume" / str(JOB_ID) / "keywords.json"
        with open(keywords_file, "w", encoding="utf-8") as f:
            json.dump(extraction_response['classified'], f, indent=4)
        
        EXTRACTION_STATUS['status'] = 'complete'
        print("✅ Background keyword extraction complete.")
    except Exception as e:
        print(f"❌ Background keyword extraction failed: {e}")
        EXTRACTION_STATUS['status'] = 'failed'
        EXTRACTION_STATUS['error'] = str(e)


@app.route("/start-extraction", methods=["POST"])
def start_extraction():
    """Starts the keyword extraction in a background thread."""
    global EXTRACTION_THREAD, EXTRACTION_STATUS

    job_dir = get_data_path() / "resume" / str(JOB_ID)
    titles_file = job_dir / "titles.json"
    keywords_file = job_dir / "keywords.json"

    if titles_file.exists() and keywords_file.exists():
        print("✅ Keyword and title files already exist. Skipping extraction.")
        EXTRACTION_STATUS = {'status': 'complete', 'error': None}
        return jsonify({"status": "complete"})

    if EXTRACTION_THREAD is None or not EXTRACTION_THREAD.is_alive():
        print("Starting keyword extraction thread...")
        EXTRACTION_THREAD = threading.Thread(target=run_keyword_extraction_task)
        EXTRACTION_THREAD.daemon = True
        EXTRACTION_THREAD.start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@app.route("/extraction-status")
def extraction_status():
    """Checks the status of the keyword extraction."""
    return jsonify(EXTRACTION_STATUS)


def run_initial_load_task():
    """Loads all necessary data in a background thread."""
    global DATA_LOADING_STATUS, JOB_DESCRIPTION, JOB_DETAILS
    try:
        DATA_LOADING_STATUS['status'] = 'pending'

        # --- Data Pre-processing ---
        # print(f"Loading job {JOB_ID}...")
        job = load_raw_job(JOB_ID)
        job_details_live = analyze_linkedin_job(job["job_link"])
        # print(f"Job details loaded: {job_details_live}")
        if not job_details_live:
            raise Exception("Failed to fetch live job details from LinkedIn.")

        JOB_DESCRIPTION = job_details_live.get("description", "Could not fetch job description.")

        evals_path = get_data_path() / "evaluator" / "evals.json"
        job_eval = {}
        try:
            with evals_path.open("r", encoding="utf-8") as f:
                evals_data = json.load(f)
            job_eval_data = next((item for item in evals_data if item.get("id") == JOB_ID), None)
            if job_eval_data:
                job_eval = job_eval_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Could not load or parse evals.json: {e}")

        JOB_DETAILS = {
            "title": job.get("title"),
            "company_name": job.get("company"),
            "location": job.get("location"),
            "posted_date": job.get("posted_date"),
            "workplace_type": job.get("workplace_type"),
            "description": JOB_DESCRIPTION,
            "score": job_eval.get("score"),
            "evaluation_grid": job_eval.get("evaluation_grid"),
            "synthesis": job_eval.get("synthesis and decision"),
        }
        # print(f"Job details: {JOB_DETAILS}")
        # --- Initial Resume Setup ---
        job_dir = get_data_path() / "resume" / f"{JOB_ID}"
        os.makedirs(job_dir, exist_ok=True)
        resume = load_cv_template()
        with open(job_dir / "resume.tex", "w", encoding="utf-8") as f:
            f.write(resume)
        compile_tex()

        DATA_LOADING_STATUS['status'] = 'complete'
        print("✅ Background initial data load complete.")
        print("JOB DETAILS COLLECTED")

    except Exception as e:
        print(f"❌ Background initial data load failed: {e}")
        DATA_LOADING_STATUS['status'] = 'failed'
        DATA_LOADING_STATUS['error'] = str(e)


@app.route("/start-initial-load", methods=["POST"])
def start_initial_load():
    """Starts the initial data loading in a background thread."""
    global DATA_LOADING_THREAD
    if DATA_LOADING_THREAD is None or not DATA_LOADING_THREAD.is_alive():
        # Avoid re-running if already complete
        if DATA_LOADING_STATUS['status'] == 'complete':
            return jsonify({"status": "complete"})
            
        print("Starting initial data load thread...")
        DATA_LOADING_THREAD = threading.Thread(target=run_initial_load_task)
        DATA_LOADING_THREAD.daemon = True
        DATA_LOADING_THREAD.start()
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@app.route("/initial-load-status")
def initial_load_status():
    """Checks the status of the initial data load."""
    return jsonify(DATA_LOADING_STATUS)


@app.route("/job-description")
def get_job_description():
    """Serves the job description text."""
    if JOB_DESCRIPTION:
        return jsonify({"description": JOB_DESCRIPTION})
    else:
        return jsonify({"error": "Job description not loaded"}), 404


@app.route("/job-details")
def get_job_details():
    """Serves the full job details."""
    print(f"Serving job details")
    if JOB_DETAILS:
        return jsonify(JOB_DETAILS)
    else:
        return jsonify({"error": "Job details not loaded"}), 404


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


@app.route("/titles")
def get_titles():
    """Serves the titles JSON file."""
    titles_file = get_data_path() / "resume" / str(JOB_ID) / "titles.json"
    try:
        return send_from_directory(titles_file.parent, titles_file.name)
    except FileNotFoundError:
        return jsonify({"error": "Titles file not found"}), 404


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
    """Main function to run the Flask app."""
    url = "http://127.0.0.1:5001/"
    print(f"Starting the dashboard server at {url}")
    print("Press CTRL+C to stop the server.")
    app.run(port=5001, debug=True)


if __name__ == "__main__":
    main()