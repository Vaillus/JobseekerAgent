const saveBtn = document.getElementById('save-btn');
const refreshBtn = document.getElementById('refresh-btn');
const reinitializeBtn = document.getElementById('reinitialize-btn');
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
    fetch("/corrector/tex")
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
     fetch("/corrector/job-description")
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
    fetch("/corrector/job-details")
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('job-viewer');
        if (data.error) {
            container.innerHTML = `<p>Error loading job details: ${data.error}</p>`;
            return;
        }

        // Clear previous content
        container.innerHTML = '';

        // --- Build the job details view safely ---
        const score = data.score !== null && data.score !== undefined ? `(${data.score})` : '';

        // Header
        const header = document.createElement('div');
        header.className = 'job-header';
        header.innerHTML = `
            <h1>${data.title || 'N/A'}</h1>
            <h2>${data.company_name || 'N/A'} - ${data.location || 'N/A'}</h2>
            <p>Posted: ${data.posted_date || 'N/A'} | Workplace: ${data.workplace_type || 'N/A'}</p>
        `;
        container.appendChild(header);
        container.appendChild(document.createElement('hr'));

        // Helper to create sections
        function createSection(title, content) {
            const h3 = document.createElement('h3');
            h3.textContent = title;
            const pre = document.createElement('pre');
            pre.textContent = content || 'Not available.';
            container.appendChild(h3);
            container.appendChild(pre);
        }

        createSection('Full Job Description', data.description);
        createSection('Synthesis and Decision', data.synthesis);
        createSection(`Evaluation Grid ${score}`, data.evaluation_grid);
    });
}

refreshBtn.addEventListener('click', () => {
    // If in TeX view, recompile. If in PDF view, just refresh.
    if (texViewer.style.display === 'block') {
        fetch("/corrector/recompile-tex", { method: 'POST' })
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

reinitializeBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to reset the TeX file to its original template? All changes will be lost.')) {
        fetch("/corrector/reinitialize-tex", { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('Reinitialization successful!');
                    texEditor.value = data.content; // Update TeX view immediately
                    setTimeout(() => {
                        refreshPdf();
                    }, 1500); // Wait for compilation
                } else {
                    alert('Reinitialization failed: ' + data.error);
                }
            });
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
        fetch("/corrector/extraction-status")
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                const keywordsPromise = fetch("/corrector/keywords").then(res => res.json());
                const titlesPromise = fetch("/corrector/titles").then(res => res.json());
                Promise.all([keywordsPromise, titlesPromise])
                    .then(([keywordsData, titlesData]) => {
                        renderData(keywordsData, titlesData);
                    })
                    .catch(error => console.error("Failed to fetch final data:", error));
            } else if (data.status === 'pending') {
                setTimeout(pollExtractionStatus, 2000);
            } else if (data.status === 'failed') {
                const loader = document.getElementById('keyword-loading-container');
                loader.innerHTML = ''; // Clear previous content
                const h4 = document.createElement('h4');
                h4.textContent = 'Extraction Failed';
                const p = document.createElement('p');
                p.textContent = data.error || 'An unknown error occurred.';
                loader.appendChild(h4);
                loader.appendChild(p);
            }
        });
    }

    fetch("/corrector/start-extraction", { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started' || data.status === 'complete') {
            pollExtractionStatus();
        } else {
            const loader = document.getElementById('keyword-loading-container');
            loader.innerHTML = ''; // Clear previous content
            const h4 = document.createElement('h4');
            h4.textContent = 'Could not start extraction';
            const p = document.createElement('p');
            p.textContent = data.error || 'An unknown error occurred.';
            loader.appendChild(h4);
            loader.appendChild(p);
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
            if (typeof title !== 'string') { return; }
            const cleanTitle = title.replace(/[\r\n]+/g, ' ').trim();
            const btn = document.createElement('button');
            btn.className = 'title-suggestion-btn';
            btn.textContent = cleanTitle;
            btn.onclick = () => updateTitle(cleanTitle, btn);
            titlesList.appendChild(btn);
        });
        titlesContainer.style.display = 'block';
    }

    const container = document.getElementById('keywords-container');
    if (!container || keywordsData.error) { return; }

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
                if (typeof keyword !== 'string') { return; }
                const cleanKeyword = keyword.replace(/[\r\n]+/g, ' ').trim();
                const labelSpan = document.createElement('span');
                labelSpan.className = 'keyword-label';
                labelSpan.classList.add(subGroupTitle.replace(/_/g, '-'));
                labelSpan.textContent = cleanKeyword;
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
    fetch("/corrector/update-title", {
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

function startAndPollRanking() {
    function pollRankingStatus() {
        fetch("/corrector/ranking-status")
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                fetch("/corrector/ranking-report")
                .then(res => res.json())
                .then(reportData => {
                    const reportContainer = document.getElementById('ranking-report');
                    reportContainer.innerHTML = '';
                    
                    const expTitle = document.createElement('h5');
                    expTitle.textContent = 'Experience Ranking';
                    reportContainer.appendChild(expTitle);
                    const expList = document.createElement('ul');
                    reportData.experience_ranking.forEach(item => {
                        const li = document.createElement('li');
                        li.textContent = item;
                        expList.appendChild(li);
                    });
                    reportContainer.appendChild(expList);

                    const skillTitle = document.createElement('h5');
                    skillTitle.textContent = 'Skill Ranking';
                    reportContainer.appendChild(skillTitle);
                    for (const category in reportData.skill_ranking) {
                        const catTitle = document.createElement('h6');
                        catTitle.textContent = category.replace(/_/g, ' ');
                        reportContainer.appendChild(catTitle);
                        const skillList = document.createElement('ul');
                        reportData.skill_ranking[category].forEach(item => {
                            const li = document.createElement('li');
                            li.textContent = item;
                            skillList.appendChild(li);
                        });
                        reportContainer.appendChild(skillList);
                    }
                    
                    alert('Ranking successful! PDF is being updated.');
                    setTimeout(() => {
                        refreshPdf();
                        viewPdfBtn.click();
                    }, 2500);
                })
                .catch(error => console.error("Failed to fetch ranking report:", error))
                .finally(() => {
                    const btn = document.getElementById('rank-resume-btn');
                    btn.textContent = 'Rank Resume';
                    btn.disabled = false;
                    document.getElementById('suggest-introductions-btn').style.display = 'block';
                });
            } else if (data.status === 'pending') {
                setTimeout(pollRankingStatus, 2000);
            } else if (data.status === 'failed') {
                const reportContainer = document.getElementById('ranking-report');
                reportContainer.innerHTML = `<p style="color: red;">Ranking failed: ${data.error || 'Unknown error'}</p>`;
                const btn = document.getElementById('rank-resume-btn');
                btn.textContent = 'Rank Resume';
                btn.disabled = false;
            }
        });
    }

    fetch("/corrector/start-ranking", { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            pollRankingStatus();
        } else {
            const reportContainer = document.getElementById('ranking-report');
            reportContainer.innerHTML = `<p style="color: red;">Could not start ranking: ${data.status}</p>`;
            const btn = document.getElementById('rank-resume-btn');
            btn.textContent = 'Rank Resume';
            btn.disabled = false;
        }
    });
}

function startAndPollIntroductions() {
    function pollIntroductionStatus() {
        fetch("/corrector/introduction-status")
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                fetch("/corrector/introduction-report")
                .then(res => res.json())
                .then(reportData => {
                    const reportContainer = document.getElementById('introduction-report');
                    const editor = document.getElementById('introduction-editor');
                    const saveBtn = document.getElementById('save-introduction-btn');
                    reportContainer.innerHTML = '';

                    if (reportData.opening_lines && reportData.opening_lines.length > 0) {
                        reportData.opening_lines.forEach((line, index) => {
                            const container = document.createElement('div');
                            container.className = 'suggestion-item';

                            const radio = document.createElement('input');
                            radio.type = 'radio';
                            radio.name = 'introduction_suggestion';
                            radio.id = `intro_${index}`;
                            radio.value = line;

                            const label = document.createElement('label');
                            label.htmlFor = `intro_${index}`;
                            label.textContent = line;

                            container.appendChild(radio);
                            container.appendChild(label);
                            reportContainer.appendChild(container);

                            radio.addEventListener('change', () => {
                                if (radio.checked) {
                                    editor.value = line;
                                    saveBtn.style.display = 'block';
                                }
                            });
                        });
                    } else {
                        reportContainer.textContent = 'No suggestions were generated.';
                    }
                    document.getElementById('introduction-container').style.display = 'block';
                })
                .catch(error => console.error("Failed to fetch introduction report:", error))
                .finally(() => {
                    const btn = document.getElementById('suggest-introductions-btn');
                    btn.textContent = 'Suggest Opening Lines';
                    btn.disabled = false;
                });
            } else if (data.status === 'pending') {
                setTimeout(pollIntroductionStatus, 2000);
            } else if (data.status === 'failed') {
                const reportContainer = document.getElementById('introduction-container');
                reportContainer.style.display = 'block';
                document.getElementById('introduction-report').innerHTML = `<p style="color: red;">Suggestion failed: ${data.error || 'Unknown error'}</p>`;
                const btn = document.getElementById('suggest-introductions-btn');
                btn.textContent = 'Suggest Opening Lines';
                btn.disabled = false;
            }
        });
    }

    fetch("/corrector/start-introduction", { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            pollIntroductionStatus();
        } else {
            const reportContainer = document.getElementById('introduction-container');
            reportContainer.style.display = 'block';
            document.getElementById('introduction-report').innerHTML = `<p style="color: red;">Could not start suggestion: ${data.status}</p>`;
            const btn = document.getElementById('suggest-introductions-btn');
            btn.textContent = 'Suggest Opening Lines';
            btn.disabled = false;
        }
    });
}

// --- Main script execution ---
console.log("DOMContentLoaded event will not fire, script running directly.");

// Element Declarations
console.log("Elements declared:", { saveBtn, refreshBtn, viewPdfBtn });

// Initial Load
function pollInitialLoadStatus() {
    fetch("/corrector/initial-load-status")
    .then(response => response.json())
    .then(data => {
        if (data.status === 'complete') {
            document.getElementById('initial-loading-container').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';
            startAndPollExtraction();
        } else if (data.status === 'pending') {
            setTimeout(pollInitialLoadStatus, 2000);
        } else if (data.status === 'failed') {
            const loader = document.getElementById('initial-loading-container');
            loader.innerHTML = '';
            const h4 = document.createElement('h4');
            h4.textContent = 'Failed to load job data';
            const p = document.createElement('p');
            p.textContent = data.error || 'An unknown error occurred.';
            loader.appendChild(h4);
            loader.appendChild(p);
        }
    });
}
    fetch("/corrector/start-initial-load", { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started' || data.status === 'complete' || data.status === 'already_running') {
            pollInitialLoadStatus();
        } else {
            const loader = document.getElementById('initial-loading-container');
            loader.innerHTML = '';
            const h4 = document.createElement('h4');
            h4.textContent = 'Could not start data loading';
            const p = document.createElement('p');
            p.textContent = data.error || 'An unknown error occurred.';
            loader.appendChild(h4);
            loader.appendChild(p);
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
    document.getElementById('run-executor-btn').addEventListener('click', function(event) {
        event.preventDefault(); // Add this line to prevent any default browser action
        const btn = this;
        const reportContainer = document.getElementById('executor-report');
        btn.textContent = 'Executing...';
        btn.disabled = true;
        reportContainer.innerHTML = '<div class="log-line">Running... please wait.</div>';

        fetch("/corrector/run-executor", { method: 'POST' })
        .then(response => {
            console.log("Received response from server:", response);
            if (!response.ok) {
                // If response is not OK (e.g., 404, 500), throw an error to be caught below
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json(); // Attempt to parse JSON
        })
        .then(data => {
            console.log("Successfully parsed JSON:", data);
            reportContainer.innerHTML = ''; // Clear the container
            if (data.success) {
                if (Array.isArray(data.report)) {
                    data.report.forEach(line => {
                        const logLine = document.createElement('div');
                        logLine.className = 'log-line';
                        logLine.textContent = line;
                        reportContainer.appendChild(logLine);
                    });
                } else if (data.report) {
                    const logLine = document.createElement('div');
                    logLine.className = 'log-line';
                    logLine.textContent = data.report;
                    reportContainer.appendChild(logLine);
                } else {
                    const logLine = document.createElement('div');
                    logLine.className = 'log-line';
                    logLine.textContent = "Execution successful, but no report was generated.";
                    reportContainer.appendChild(logLine);
                }
                document.getElementById('rank-resume-btn').style.display = 'block';


                alert('Execution successful! PDF is being updated.');
                setTimeout(() => {
                    refreshPdf();
                    viewPdfBtn.click();
                }, 2500); // Increased delay to 2.5 seconds
            } else {
                const safeError = String(data.error || 'Unknown error');
                const errorLine = document.createElement('div');
                errorLine.className = 'log-line';
                errorLine.style.color = 'red';
                errorLine.textContent = "Error during execution: " + safeError;
                reportContainer.appendChild(errorLine);
                alert('Execution failed: ' + safeError.substring(0, 500));
            }
        })
        .catch(error => {
            // This will catch network errors and errors from the .then() blocks
            console.error('Fetch error:', error);
            reportContainer.innerHTML = ''; // Clear the container
            const errorLine = document.createElement('div');
            errorLine.className = 'log-line';
            errorLine.style.color = 'red';
            errorLine.textContent = "A critical error occurred: " + error.message;
            reportContainer.appendChild(errorLine);
            alert("A critical error occurred. Please check the browser's console for details.");
        })
        .finally(() => {
            btn.textContent = 'Run Keyword Executor';
            btn.disabled = false;
        });
    });

    document.getElementById('rank-resume-btn').addEventListener('click', function() {
        const btn = this;
        btn.textContent = 'Ranking...';
        btn.disabled = true;
        
        startAndPollRanking();
    });

    document.getElementById('suggest-introductions-btn').addEventListener('click', function() {
        const btn = this;
        btn.textContent = 'Suggesting...';
        btn.disabled = true;
        document.getElementById('introduction-container').style.display = 'block';
        document.getElementById('introduction-report').innerHTML = '<p>Generating suggestions...</p>';
        startAndPollIntroductions();
    });

    document.getElementById('save-introduction-btn').addEventListener('click', function() {
        const introductionText = document.getElementById('introduction-editor').value;
        if (!introductionText.trim()) {
            alert('Introduction cannot be empty.');
            return;
        }

        const btn = this;
        btn.textContent = 'Saving...';
        btn.disabled = true;

        fetch("/corrector/save-introduction", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ introduction: introductionText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Introduction saved successfully! PDF is being updated.');
                setTimeout(() => {
                    refreshPdf();
                    viewPdfBtn.click();
                }, 2500);
            } else {
                alert('Error saving introduction: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Save introduction error:', error);
            alert('A critical error occurred while saving the introduction.');
        })
        .finally(() => {
            btn.textContent = 'Validate';
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

        fetch("/corrector/save-validated-keywords", {
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
        fetch("/corrector/save-tex", {
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
