// No more DOMContentLoaded wrapper

let highlighter; // Declare highlighter in a broader scope
let currentContext = 'resume'; // Tracks whether viewing 'resume' or 'cover-letter'

// --- Utility Functions ---

function refreshPdf() {
    const pdfViewer = document.getElementById('pdf-viewer');
    if (pdfViewer) {
        const url = new URL(pdfViewer.src);
        url.searchParams.set('t', new Date().getTime());
        pdfViewer.src = url.href;
    }
    refreshTex();
}

function refreshTex() {
    refreshTexForContext(currentContext);
}

function refreshTexForContext(context) {
    const texEditor = document.getElementById('tex-editor');
    const endpoint = context === 'cover-letter' ? '/customizer/cover-letter-tex' : '/customizer/tex';
    
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            if (data.content) {
                texEditor.value = data.content;
            } else {
                texEditor.value = "Error loading TeX file: " + (data.error || "Unknown error");
            }
        });
}

function switchToDocumentContext(context) {
    currentContext = context;
    const pdfViewer = document.getElementById('pdf-viewer');
    const filename = context === 'cover-letter' ? 'cover-letter.pdf' : 'resume.pdf';
    const url = `/customizer/pdf/${filename}?t=${new Date().getTime()}`;
    pdfViewer.src = url;
    
    // If TeX viewer is visible, refresh its content
    if (document.getElementById('tex-viewer').style.display === 'block') {
        refreshTexForContext(context);
    }
}

function fetchJobDetails(data) {
    console.log("--- Populating Job Details view with received data ---", data);
    const container = document.getElementById('job-viewer');
    if (!container) return;
    if (!data || data.error) {
        container.innerHTML = `<p>Error loading job details: ${data ? data.error : 'No data received.'}</p>`;
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
        <p><a href="${ data.job_link || '#' }" target="_blank">View Original Job Post</a></p>
        <p>Posted: ${data.posted_date || 'N/A'} | Workplace: ${data.workplace_type || 'N/A'}</p>
    `;
    container.appendChild(header);
    container.appendChild(document.createElement('hr'));

    // Helper to create sections
    function createSection(title, content, isHtml = false) {
        const h3 = document.createElement('h3');
        h3.textContent = title;
        container.appendChild(h3);

        if (isHtml) {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'job-description-content'; // for CSS styling
            contentDiv.innerHTML = content || 'Not available.';
            container.appendChild(contentDiv);
        } else {
            const pre = document.createElement('pre');
            pre.textContent = content || 'Not available.';
            container.appendChild(pre);
        }
    }

    createSection('Full Job Description', data.description, true);

    // Use the data directly from the initial load
    createSection('Synthesis and Decision', data.synthesis, true);

    const gridTitle = document.createElement('h3');
    gridTitle.textContent = 'Evaluation Grid';
    container.appendChild(gridTitle);

    const gridContainer = document.createElement('div');
    gridContainer.innerHTML = formatEvaluationGrid(data.evaluation_grid);
    container.appendChild(gridContainer);

    initializeHighlighter();
}

function initializeHighlighter() {
    if (typeof rangy === 'undefined' || !rangy.init) {
        console.error("Rangy library is not loaded. Highlighting will be disabled. Please check for 404 errors in the browser's Network tab.");
        return;
    }
    rangy.init();

    highlighter = rangy.createHighlighter();
    
    highlighter.addClassApplier(rangy.createClassApplier("manual-highlight", {
        ignoreWhiteSpace: true,
        tagNames: ["span"]
    }));

    const jobViewerEl = document.getElementById('job-viewer');
    if (!jobViewerEl) return;

    // Use a flag to prevent re-attaching listeners
    if (jobViewerEl.dataset.highlighterInitialized) return;
    jobViewerEl.dataset.highlighterInitialized = 'true';

    jobViewerEl.addEventListener('mouseup', () => {
        const selection = rangy.getSelection();
        const selectedText = selection.toString();
        
        console.log("Mouse button released.");

        if (selectedText) {
            console.log("Text selected:", selectedText);
            highlighter.highlightSelection("manual-highlight");
        } else {
            console.log("No text was selected.");
        }
    });

    jobViewerEl.addEventListener('mousedown', (e) => {
        if (e.button === 2 && e.target.classList.contains('manual-highlight')) {
            e.preventDefault();
            const h = highlighter.getHighlightForElement(e.target);
            if (h) {
                highlighter.removeHighlights( [h] );
            }
        }
    });
}


function formatEvaluationGrid(gridData) {
    if (!gridData) {
        return '<pre>Not available.</pre>';
    }
    if (typeof gridData === 'string') {
        return `<pre>${gridData}</pre>`;
    }
    if (Array.isArray(gridData)) {
        let html = '<div class="evaluation-grid-container">';
        gridData.forEach(item => {
            let scoreClass = '';
            let score = Math.round(parseFloat(item.score));
            score = Math.max(-3, Math.min(3, score)); // Clamp score

            if (!isNaN(score) && score !== 0) {
                if (score > 0) {
                    scoreClass = `evaluation-item-positive-${score}`;
                } else { // score < 0
                    scoreClass = `evaluation-item-negative-${Math.abs(score)}`;
                }
            }

            html += `<div class="evaluation-item ${scoreClass}">`;

            for (const [key, value] of Object.entries(item)) {
                if (key === 'criteria' || key === 'score') {
                    html += `<div class="evaluation-field"><strong>${key}:</strong> ${value}</div>`;
                }
            }
            html += '</div>';
        });
        html += '</div>';
        return html;
    }
    return `<pre>${JSON.stringify(gridData, null, 2)}</pre>`;
}


function checkValidationState() {
    const finalizeBtn = document.getElementById('finalize-btn');
    if (!finalizeBtn) return;
    const groups = document.querySelectorAll('.keyword-group');
    if (groups.length === 0) {
        finalizeBtn.disabled = true;
        return;
    }
    const allValidated = Array.from(groups).every(group => group.classList.contains('validated'));
    finalizeBtn.disabled = !allValidated;
}

// --- Polling and Data Loading Functions ---

function startAndPollExtraction() {
    function pollExtractionStatus() {
        fetch("/customizer/extraction-status")
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                const keywordsPromise = fetch("/customizer/keywords").then(res => res.json());
                const titlesPromise = fetch("/customizer/titles").then(res => res.json());
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

    fetch("/customizer/start-extraction", { method: 'POST' })
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
    
    // Check if we have validated data
    const isValidated = keywordsData.validated === true;
    const dataToRender = isValidated ? keywordsData.keywords : keywordsData;
    
    for (const groupTitle in dataToRender) {
        const groupData = dataToRender[groupTitle];
        const groupDiv = document.createElement('div');
        groupDiv.className = 'keyword-group';
        
        // If validated, mark as validated from the start
        if (isValidated) {
            groupDiv.classList.add('validated');
        }
        
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
        
        // Handle validated data structure (flat keywords array)
        if (isValidated) {
            const keywords = groupData.keywords || [];
            const instructions = groupData.instructions || '';
            
            const subGroupDiv = document.createElement('div');
            subGroupDiv.className = 'keyword-subgroup';
            
            const labelsDiv = document.createElement('div');
            labelsDiv.className = 'keyword-labels';
            keywords.forEach(keyword => {
                if (typeof keyword !== 'string') { return; }
                const cleanKeyword = keyword.replace(/[\r\n]+/g, ' ').trim();
                const labelSpan = document.createElement('span');
                labelSpan.className = 'keyword-label';
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
            
            // Add input area with saved instructions
            const inputArea = document.createElement('div');
            inputArea.className = 'input-area';
            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = 'Add a note...';
            input.value = instructions; // Pre-fill with saved instructions
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
        } else {
            // Handle raw extraction data structure (nested subgroups)
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
            
            // Add input area (empty for new data)
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
        }
        
        container.appendChild(groupDiv);
    }
    
    // Update finalize button state
    checkValidationState();
}

function updateTitle(title, clickedButton = null) {
    document.querySelectorAll('.title-suggestion-btn').forEach(b => b.classList.remove('selected'));
    if (clickedButton) {
        clickedButton.classList.add('selected');
    }
    fetch("/customizer/update-title", {
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
                // Refresh ranking data after PDF update
                setTimeout(() => refreshRankingData(), 2000);
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

function updateExperienceBlocksOrder(experienceRanking) {
    const container = document.getElementById('experience-blocks-container');
    if (!container) return;
    
    const blocks = Array.from(container.querySelectorAll('.experience-block'));
    const blockMap = {};
    blocks.forEach(block => {
        blockMap[block.dataset.exp] = block;
    });
    
    // Clear container
    container.innerHTML = '';
    
    // Re-add blocks in the new order
    experienceRanking.forEach(expName => {
        if (blockMap[expName]) {
            container.appendChild(blockMap[expName]);
        }
    });
}

function startAndPollRanking() {
    function pollRankingStatus() {
        fetch("/customizer/ranking-status")
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                fetch("/customizer/ranking-report")
                .then(res => res.json())
                .then(reportData => {
                    // Update the visual order of experience blocks
                    updateExperienceBlocksOrder(reportData.experience_ranking);
                    
                    // Update the visual order of skill blocks
                    updateSkillsBlocksOrder(reportData.skill_ranking);
                    
                    setTimeout(() => {
                        refreshPdf();
                        document.getElementById('view-pdf-btn').click();
                        // Refresh skills after PDF update to catch any new skills
                        setTimeout(() => refreshRankingData(), 3000);
                    }, 2500);
                })
                .catch(error => console.error("Failed to fetch ranking report:", error))
                .finally(() => {
                    const btn = document.getElementById('auto-rank-btn');
                    btn.textContent = 'Auto-Rank with AI';
                    btn.disabled = false;
                    document.getElementById('suggest-introductions-btn').style.display = 'block';
                });
            } else if (data.status === 'pending') {
                setTimeout(pollRankingStatus, 2000);
            } else if (data.status === 'failed') {
                alert('Ranking failed: ' + (data.error || 'Unknown error'));
                const btn = document.getElementById('auto-rank-btn');
                btn.textContent = 'Auto-Rank with AI';
                btn.disabled = false;
            }
        });
    }

    fetch("/customizer/start-ranking", { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            pollRankingStatus();
        } else {
            alert('Could not start ranking: ' + data.status);
            const btn = document.getElementById('auto-rank-btn');
            btn.textContent = 'Auto-Rank with AI';
            btn.disabled = false;
        }
    });
}

function startAndPollIntroductions() {
    function pollIntroductionStatus() {
        fetch("/customizer/introduction-status")
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                fetch("/customizer/introduction-report")
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

    fetch("/customizer/start-introduction", { method: 'POST' })
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

function loadCoverLetterContent() {
    fetch("/customizer/cover-letter-content")
    .then(response => response.json())
    .then(data => {
        if (data.success && data.content) {
            const editor = document.getElementById('cover-letter-editor');
            const container = document.getElementById('cover-letter-editor-container');
            editor.value = data.content;
            container.style.display = 'block';
        }
    })
    .catch(error => {
        console.log('No cover letter found yet:', error);
    });
}

function startAndPollCoverLetter() {
    function pollCoverLetterStatus() {
        fetch("/customizer/cover-letter-status")
        .then(response => response.json())
        .then(data => {
            if (data.status === 'complete') {
                const statusMessage = document.getElementById('cover-letter-status-message');
                statusMessage.innerHTML = '<p style="color: green;">Cover letter generated successfully!</p>';
                
                // Clear progress message
                const progressDiv = document.getElementById('cover-letter-progress');
                progressDiv.textContent = '';
                
                // Display the cover letter content in editor
                if (data.content) {
                    const editor = document.getElementById('cover-letter-editor');
                    const container = document.getElementById('cover-letter-editor-container');
                    editor.value = data.content;
                    container.style.display = 'block';
                }
                
                const btn = document.getElementById('generate-cover-letter-btn');
                btn.textContent = 'Generate Cover Letter';
                btn.disabled = false;
            } else if (data.status === 'pending') {
                // Update progress message if available
                const progressDiv = document.getElementById('cover-letter-progress');
                if (data.message) {
                    progressDiv.textContent = data.message;
                }
                setTimeout(pollCoverLetterStatus, 2000);
            } else if (data.status === 'failed') {
                const statusMessage = document.getElementById('cover-letter-status-message');
                statusMessage.innerHTML = `<p style="color: red;">Generation failed: ${data.error || 'Unknown error'}</p>`;
                
                // Clear progress message
                const progressDiv = document.getElementById('cover-letter-progress');
                progressDiv.textContent = '';
                
                const btn = document.getElementById('generate-cover-letter-btn');
                btn.textContent = 'Generate Cover Letter';
                btn.disabled = false;
            }
        });
    }

    fetch("/customizer/start-cover-letter", { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            pollCoverLetterStatus();
        } else {
            const statusMessage = document.getElementById('cover-letter-status-message');
            statusMessage.innerHTML = `<p style="color: red;">Could not start generation: ${data.status}</p>`;
            const btn = document.getElementById('generate-cover-letter-btn');
            btn.textContent = 'Generate Cover Letter';
            btn.disabled = false;
        }
    });
}

function saveCoverLetter() {
    const editor = document.getElementById('cover-letter-editor');
    const content = editor.value;
    const btn = document.getElementById('save-cover-letter-btn');
    const statusMessage = document.getElementById('cover-letter-status-message');
    
    btn.textContent = 'Saving...';
    btn.disabled = true;
    
    fetch("/customizer/save-cover-letter", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusMessage.innerHTML = '<p style="color: green;">Cover letter saved successfully!</p>';
            setTimeout(() => { statusMessage.innerHTML = ''; }, 3000);
        } else {
            statusMessage.innerHTML = `<p style="color: red;">Save failed: ${data.error || 'Unknown error'}</p>`;
        }
    })
    .catch(error => {
        statusMessage.innerHTML = `<p style="color: red;">Save failed: ${error.message}</p>`;
    })
    .finally(() => {
        btn.textContent = 'Save Cover Letter';
        btn.disabled = false;
    });
}

function getExperienceOrder() {
    const container = document.getElementById('experience-blocks-container');
    if (!container) return { experience_order: [], hidden_experiences: [] };
    
    const blocks = Array.from(container.querySelectorAll('.experience-block'));
    
    return {
        experience_order: blocks.map(block => block.dataset.exp),
        hidden_experiences: blocks
            .filter(block => block.dataset.hidden === 'true')
            .map(block => block.dataset.exp)
    };
}

function loadCurrentSkills() {
    fetch("/customizer/get-current-skills")
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error("Error loading skills:", data.error);
            return;
        }
        
        ['expertise', 'programming_language', 'technologies'].forEach(category => {
            const container = document.getElementById(`${category}-blocks-container`);
            if (!container) return;
            
            container.innerHTML = '';
            const skills = data[category] || [];
            
            skills.forEach(skill => {
                const block = document.createElement('div');
                block.className = 'skill-block';
                block.draggable = true;
                block.dataset.skill = skill;
                
                // Create text node for the skill
                const textSpan = document.createElement('span');
                textSpan.className = 'skill-text';
                textSpan.textContent = skill;
                block.appendChild(textSpan);
                
                // Create remove button
                const removeBtn = document.createElement('button');
                removeBtn.className = 'skill-remove-btn';
                removeBtn.innerHTML = '&times;';
                removeBtn.onclick = (e) => {
                    e.stopPropagation();
                    block.remove();
                };
                block.appendChild(removeBtn);
                
                container.appendChild(block);
            });
        });
        
        initializeSkillsDragAndDrop();
    })
    .catch(error => console.error("Failed to load skills:", error));
}

function initializeSkillsDragAndDrop() {
    const categories = ['expertise', 'programming_language', 'technologies'];
    
    categories.forEach(category => {
        const container = document.getElementById(`${category}-blocks-container`);
        if (!container) return;
        
        // Use SortableJS for smooth drag-and-drop with animations
        // Using 'group' allows dragging skills between different categories
        new Sortable(container, {
            group: 'skills',  // Shared group allows cross-category dragging
            animation: 150,
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            dragClass: 'sortable-drag',
            easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
            // No onEnd needed - we get the order when user clicks Apply
        });
    });
}

function getSkillsOrder() {
    const result = {};
    ['expertise', 'programming_language', 'technologies'].forEach(category => {
        const container = document.getElementById(`${category}-blocks-container`);
        if (!container) {
            result[category] = [];
            return;
        }
        const blocks = container.querySelectorAll('.skill-block');
        // Use dataset.skill which is set when the block is created
        result[category] = Array.from(blocks).map(block => block.dataset.skill);
    });
    return result;
}

function updateSkillsBlocksOrder(skillRanking) {
    for (const [category, skills] of Object.entries(skillRanking)) {
        const container = document.getElementById(`${category}-blocks-container`);
        if (!container) continue;
        
        const blocks = Array.from(container.querySelectorAll('.skill-block'));
        const blockMap = {};
        blocks.forEach(block => {
            blockMap[block.dataset.skill] = block;
        });
        
        container.innerHTML = '';
        
        skills.forEach(skillName => {
            if (blockMap[skillName]) {
                container.appendChild(blockMap[skillName]);
            }
        });
    }
}

function loadCurrentExperienceOrder() {
    fetch("/customizer/get-current-experience-order")
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error("Error loading experience order:", data.error);
            return;
        }
        
        if (data.experience_order) {
            updateExperienceBlocksOrder(data.experience_order);
        }
        
        // Apply hidden state to blocks
        if (data.hidden_experiences) {
            const container = document.getElementById('experience-blocks-container');
            if (container) {
                // Reset all blocks to visible first
                container.querySelectorAll('.experience-block').forEach(block => {
                    block.dataset.hidden = 'false';
                    const btn = block.querySelector('.experience-toggle-btn');
                    if (btn) btn.textContent = '👁';
                });
                
                // Then mark hidden ones
                data.hidden_experiences.forEach(expName => {
                    const block = container.querySelector(`[data-exp="${expName}"]`);
                    if (block) {
                        block.dataset.hidden = 'true';
                        const btn = block.querySelector('.experience-toggle-btn');
                        if (btn) btn.textContent = '👁‍🗨';
                    }
                });
            }
        }
    })
    .catch(error => console.error("Failed to load experience order:", error));
}

function refreshRankingData() {
    console.log("Refreshing ranking data (experiences and skills)...");
    loadCurrentExperienceOrder();
    loadCurrentSkills();
}

function initializeDragAndDrop() {
    const container = document.getElementById('experience-blocks-container');
    if (!container) return;
    
    // Use SortableJS for smooth drag-and-drop with animations
    new Sortable(container, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        dragClass: 'sortable-drag',
        easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
        // No onEnd needed - we get the order when user clicks Apply
    });
    
    // Add event listeners for toggle buttons
    container.querySelectorAll('.experience-toggle-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const block = btn.closest('.experience-block');
            if (!block) return;
            
            const isHidden = block.dataset.hidden === 'true';
            block.dataset.hidden = isHidden ? 'false' : 'true';
            btn.textContent = isHidden ? '👁' : '👁‍🗨';
        };
    });
}

function pollInitialLoadStatus() {
    console.log("Polling for initial load status...");
    fetch("/customizer/initial-load-status")
    .then(response => response.json())
    .then(data => {
        console.log("Received status:", data.status);
        if (data.status === 'complete') {
            console.log("Status is 'complete'. Hiding loader and starting keyword extraction.");
            console.log("--- Received Job Details upon completion ---", data.job_details); // Log the data here
            
            document.getElementById('initial-loading-container').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';
            document.querySelector('.tabs').style.display = 'flex'; // Show the tabs
            
            // Store job details globally to be used by fetchJobDetails
            window.jobDetailsData = data.job_details;

            // If job view is active, populate it now that data is available.
            const jobViewer = document.getElementById('job-viewer');
            if (jobViewer.style.display === 'block') {
                console.log("Job viewer is active, populating with fetched data.");
                fetchJobDetails(window.jobDetailsData);
            }

            startAndPollExtraction();
            
            // Initialize drag-and-drop for the ranking section
            initializeDragAndDrop();
            
            // Load current order from resume
            loadCurrentExperienceOrder();
            loadCurrentSkills();
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


// --- Event Delegation for All Actions ---

document.body.addEventListener('click', function(event) {
    const target = event.target;
    // Use .closest() to handle clicks on icons inside buttons
    const button = target.closest('button');
    if (!button) return; // Exit if the click was not on or inside a button

    const id = button.id;

    // --- View Switching Logic ---
    if (id === 'view-pdf-btn') {
        document.getElementById('pdf-viewer').style.display = 'block';
        document.getElementById('tex-viewer').style.display = 'none';
        document.getElementById('job-viewer').style.display = 'none';
        document.getElementById('refresh-btn').style.display = 'inline-block';
        document.getElementById('save-btn').style.display = 'none';
        button.classList.add('active');
        document.getElementById('view-tex-btn').classList.remove('active');
        document.getElementById('view-job-btn').classList.remove('active');
        return;
    }

    if (id === 'view-tex-btn') {
        document.getElementById('pdf-viewer').style.display = 'none';
        document.getElementById('tex-viewer').style.display = 'block';
        document.getElementById('job-viewer').style.display = 'none';
        document.getElementById('refresh-btn').style.display = 'inline-block';
        document.getElementById('save-btn').style.display = 'inline-block';
        button.classList.add('active');
        document.getElementById('view-pdf-btn').classList.remove('active');
        document.getElementById('view-job-btn').classList.remove('active');
        if (!document.getElementById('tex-editor').value) {
            refreshTex();
        }
        return;
    }

    if (id === 'view-job-btn') {
        document.getElementById('pdf-viewer').style.display = 'none';
        document.getElementById('tex-viewer').style.display = 'none';
        const jobViewer = document.getElementById('job-viewer');
        jobViewer.style.display = 'block';
        document.getElementById('refresh-btn').style.display = 'none';
        document.getElementById('save-btn').style.display = 'none';
        button.classList.add('active');
        document.getElementById('view-pdf-btn').classList.remove('active');
        document.getElementById('view-tex-btn').classList.remove('active');
        
        // Only populate if data is available and viewer is still showing the loader.
        // The check for children ensures we don't re-render over existing content.
        if (window.jobDetailsData && jobViewer.children.length <= 2) { 
            console.log("Job data is ready, populating viewer.");
            fetchJobDetails(window.jobDetailsData);
        }
        return;
    }

    if (id === 'save-highlights-btn') {
        if (!highlighter) {
            alert("Highlighter is not initialized. Please click on the 'Job' tab first.");
            return;
        }
        const highlightedTexts = highlighter.highlights.map(h => h.getText());
        fetch("/customizer/save-highlights", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ highlights: highlightedTexts })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Highlights saved successfully!');
            } else {
                alert('Error saving highlights: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Failed to save highlights:', error);
            alert('An error occurred while saving highlights.');
        });
        return;
    }

    // --- Main Controls ---
    if (id === 'refresh-btn') {
        if (document.getElementById('tex-viewer').style.display === 'block') {
            refreshTex();
            fetch("/customizer/recompile-tex", { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        setTimeout(() => {
                            refreshPdf();
                            // Refresh ranking data after PDF update
                            setTimeout(() => refreshRankingData(), 2000);
                        }, 1500);
                    } else {
                        alert('Recompilation failed: ' + data.error);
                    }
                });
        } else {
            refreshPdf();
            // Refresh ranking data after PDF update
            setTimeout(() => refreshRankingData(), 2000);
        }
        return;
    }

    if (id === 'save-btn') {
        const content = document.getElementById('tex-editor').value;
        button.textContent = 'Saving...';
        button.disabled = true;
        fetch("/customizer/save-tex", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('tex-editor').value = "";
                setTimeout(() => {
                    document.getElementById('view-pdf-btn').click();
                    refreshPdf();
                    // Refresh ranking data after PDF update
                    setTimeout(() => refreshRankingData(), 2000);
                }, 1500);
            } else {
                alert('Error saving file: ' + (data.error || 'Unknown error'));
            }
        })
        .finally(() => {
            button.textContent = 'Save';
            button.disabled = false;
        });
        return;
    }
    
    if (id === 'reinitialize-btn') {
        if (confirm('Are you sure you want to reset the TeX file to its original template? All changes will be lost.')) {
            fetch("/customizer/reinitialize-tex", { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('tex-editor').value = data.content; // Update TeX view immediately
                        setTimeout(refreshPdf, 1500); // Wait for compilation
                    } else {
                        alert('Reinitialization failed: ' + data.error);
                    }
                });
        }
        return;
    }

    // --- Tab Switching ---
    if (button.classList.contains('tab-btn')) {
        const tabId = button.dataset.tab;
        
        // Switch document context based on tab
        if (tabId === 'cover-letter') {
            switchToDocumentContext('cover-letter');
        } else {
            switchToDocumentContext('resume');
        }
        
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.style.display = tab.id === `${tabId}-tab` ? 'block' : 'none';
        });
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');
        
        // Initialize drag-and-drop when switching to Ranker tab
        if (tabId === 'ranker') {
            const rankingSection = document.getElementById('ranking-section');
            if (rankingSection && rankingSection.style.display !== 'none') {
                initializeDragAndDrop();
            }
            const skillsSection = document.getElementById('skills-ranking-section');
            if (skillsSection && skillsSection.style.display !== 'none') {
                initializeSkillsDragAndDrop();
            }
        }
        
        // Load cover letter content when switching to Cover Letter tab
        if (tabId === 'cover-letter') {
            loadCoverLetterContent();
        }
        return;
    }
    
    // --- Actions within Tabs ---
    if (id === 'apply-custom-title-btn') {
        const input = document.getElementById('custom-title-input');
        const customTitle = input.value.trim();
        if (customTitle) {
            updateTitle(customTitle);
        } else {
            alert('Please enter a custom title.');
        }
        return;
    }
    
    if (id === 'finalize-btn') {
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

        button.textContent = 'Saving...';
        button.disabled = true;

        fetch("/customizer/save-validated-keywords", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(finalData)
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert('Error saving keywords: ' + (data.error || 'Unknown error'));
            }
        })
        .finally(() => {
            button.textContent = 'Finalize & Save Keywords';
            checkValidationState();
        });
        return;
    }

    if (id === 'run-executor-btn') {
        event.preventDefault();
        const reportContainer = document.getElementById('executor-report');
        button.textContent = 'Executing...';
        button.disabled = true;
        reportContainer.innerHTML = '<div class="log-line">Running... please wait.</div>';

        fetch("/customizer/run-executor", { method: 'POST' })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            reportContainer.innerHTML = '';
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
                    reportContainer.innerHTML = '<div class="log-line">Execution successful, but no report was generated.</div>';
                }

                setTimeout(() => {
                    refreshPdf();
                    document.getElementById('view-pdf-btn').click();
                    // Refresh ranking data after PDF update (important for skill changes)
                    setTimeout(() => refreshRankingData(), 3000);
                }, 2500);
            } else {
                const safeError = String(data.error || 'Unknown error');
                reportContainer.innerHTML = `<div class="log-line" style="color: red;">Error during execution: ${safeError}</div>`;
                alert('Execution failed: ' + safeError.substring(0, 500));
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            reportContainer.innerHTML = `<div class="log-line" style="color: red;">A critical error occurred: ${error.message}</div>`;
            alert("A critical error occurred. Please check the browser's console for details.");
        })
        .finally(() => {
            button.textContent = 'Run Keyword Executor';
            button.disabled = false;
        });
        return;
    }

    if (id === 'auto-rank-btn') {
        button.textContent = 'Ranking...';
        button.disabled = true;
        startAndPollRanking();
        return;
    }
    
    if (id === 'apply-manual-ranking-btn') {
        button.textContent = 'Applying...';
        button.disabled = true;
        
        const experienceData = getExperienceOrder();
        const skillRanking = getSkillsOrder();
        
        // Appliquer d'abord les expériences (avec hidden state)
        fetch("/customizer/apply-manual-ranking", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                experience_order: experienceData.experience_order,
                hidden_experiences: experienceData.hidden_experiences
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                throw new Error(data.error || 'Failed to apply experience ranking');
            }
            // Puis appliquer les skills
            return fetch("/customizer/apply-manual-skill-ranking", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ skill_ranking: skillRanking })
            });
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Manual ranking applied successfully (experiences + skills).');
                
                document.getElementById('suggest-introductions-btn').style.display = 'block';
                
                setTimeout(() => {
                    refreshPdf();
                    document.getElementById('view-pdf-btn').click();
                    setTimeout(() => refreshRankingData(), 3000);
                }, 2500);
            } else {
                alert('Error applying manual ranking: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Failed to apply manual ranking:', error);
            alert('An error occurred while applying the manual ranking: ' + error.message);
        })
        .finally(() => {
            button.textContent = 'Apply Manual Order';
            button.disabled = false;
        });
        return;
    }
    
    if (id === 'suggest-introductions-btn') {
        button.textContent = 'Suggesting...';
        button.disabled = true;
        document.getElementById('introduction-container').style.display = 'block';
        document.getElementById('introduction-report').innerHTML = '<p>Generating suggestions...</p>';
        startAndPollIntroductions();
        return;
    }
    
    if (id === 'generate-cover-letter-btn') {
        button.textContent = 'Generating...';
        button.disabled = true;
        const statusMessage = document.getElementById('cover-letter-status-message');
        statusMessage.innerHTML = '<p>Generating cover letter, please wait...</p>';
        startAndPollCoverLetter();
        return;
    }
    
    if (id === 'save-cover-letter-btn') {
        saveCoverLetter();
        return;
    }
    
    if (id === 'save-introduction-btn') {
        const introductionText = document.getElementById('introduction-editor').value;
        if (!introductionText.trim()) {
            alert('Introduction cannot be empty.');
            return;
        }

        button.textContent = 'Saving...';
        button.disabled = true;

        fetch("/customizer/save-introduction", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ introduction: introductionText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setTimeout(() => {
                    refreshPdf();
                    document.getElementById('view-pdf-btn').click();
                    // Refresh ranking data after PDF update
                    setTimeout(() => refreshRankingData(), 3000);
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
            button.textContent = 'Validate';
            button.disabled = false;
        });
        return;
    }
    
    if (id === 'delete-publications-btn') {
        if (!confirm('Are you sure you want to delete the Publications section? This action cannot be undone.')) {
            return;
        }

        button.textContent = 'Deleting...';
        button.disabled = true;

        fetch("/customizer/delete-publications", {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Publications section deleted successfully!');
                setTimeout(() => {
                    refreshPdf();
                    document.getElementById('view-pdf-btn').click();
                    // Refresh ranking data after PDF update
                    setTimeout(() => refreshRankingData(), 2000);
                }, 1500);
            } else {
                alert('Error deleting publications: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Delete publications error:', error);
            alert('A critical error occurred while deleting the publications section.');
        })
        .finally(() => {
            button.textContent = 'Delete Publications';
            button.disabled = false;
        });
        return;
    }
});


// --- Initial Script Execution ---
console.log("Triggering start-initial-load...");
fetch("/customizer/start-initial-load", { method: 'POST' })
.then(response => response.json())
.then(data => {
    console.log("Response from start-initial-load:", data.status);
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
