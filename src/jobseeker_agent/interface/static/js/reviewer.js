// Tab switching functionality
document.querySelectorAll('.sidebar-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;
        
        // Update button states
        document.querySelectorAll('.sidebar-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update content visibility
        document.querySelectorAll('.sidebar-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${targetTab}-tab`).classList.add('active');
    });
});

// Job item click handlers
document.querySelectorAll('.job-item').forEach(item => {
    item.addEventListener('click', () => {
        const jobId = item.dataset.jobId;
        displayJobDetails(jobId);
        document.querySelectorAll('.job-item').forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');
    });
});

// Scraping functionality
let scrapingInterval = null;

// Destinations state
let scrapingDestinations = [];

// Auto-review flag after scraping
let autoEvaluateAfterScrape = false;

// Load destinations config on startup
fetch('/scrape/config')
    .then(response => response.json())
    .then(data => {
        if (data && Array.isArray(data.destinations)) {
            scrapingDestinations = data.destinations;
            renderDestinations();
        }
    })
    .catch(err => console.error('Failed to load scraping config:', err));

function renderDestinations() {
    const list = document.getElementById('destinations-list');
    if (!list) return;
    list.innerHTML = '';

    scrapingDestinations.forEach(dest => {
        const row = document.createElement('div');
        row.className = `destination-item ${dest.enabled ? '' : 'disabled'}`;

        const info = document.createElement('div');
        info.className = 'destination-info';
        info.textContent = `${dest.location} (${dest.remote_type})`;

        const toggle = document.createElement('button');
        toggle.className = 'destination-toggle';
        toggle.textContent = dest.enabled ? '✓' : '✗';
        toggle.addEventListener('click', () => {
            dest.enabled = !dest.enabled;
            persistDestinations();
            renderDestinations();
        });

        const editBtn = document.createElement('button');
        editBtn.className = 'destination-edit-btn';
        editBtn.textContent = 'Edit';
        editBtn.addEventListener('click', () => showInlineForm(dest));

        row.appendChild(info);
        const actions = document.createElement('div');
        actions.appendChild(toggle);
        actions.appendChild(editBtn);
        row.appendChild(actions);
        list.appendChild(row);
    });
}

function showInlineForm(dest = null) {
    const form = document.getElementById('destination-inline-form');
    if (!form) return;
    form.style.display = 'block';

    const locInput = document.getElementById('new-destination-location');
    const typeSelect = document.getElementById('new-destination-remote-type');
    const confirmBtn = document.getElementById('confirm-add-destination');
    const cancelBtn = document.getElementById('cancel-add-destination');

    if (dest) {
        locInput.value = dest.location;
        typeSelect.value = dest.remote_type;
        confirmBtn.textContent = 'Save';
    } else {
        locInput.value = '';
        typeSelect.value = 'any';
        confirmBtn.textContent = 'Add';
    }

    const onConfirm = () => {
        const location = locInput.value.trim();
        const remoteType = typeSelect.value;
        if (!location) {
            alert('Please enter a location');
            return;
        }
        if (dest) {
            dest.location = location;
            dest.remote_type = remoteType;
        } else {
            const newId = scrapingDestinations.length > 0 ? Math.max(...scrapingDestinations.map(d => d.id || 0)) + 1 : 1;
            scrapingDestinations.push({ id: newId, location, remote_type: remoteType, enabled: true });
        }
        form.style.display = 'none';
        persistDestinations();
        renderDestinations();
        // Cleanup handlers
        confirmBtn.removeEventListener('click', onConfirm);
        cancelBtn.removeEventListener('click', onCancel);
    };

    const onCancel = () => {
        form.style.display = 'none';
        confirmBtn.removeEventListener('click', onConfirm);
        cancelBtn.removeEventListener('click', onCancel);
    };

    confirmBtn.addEventListener('click', onConfirm);
    cancelBtn.addEventListener('click', onCancel);
}

const addDestBtn = document.getElementById('add-destination-btn');
if (addDestBtn) {
    addDestBtn.addEventListener('click', () => showInlineForm());
}

function persistDestinations() {
    fetch('/scrape/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destinations: scrapingDestinations })
    }).catch(err => console.error('Failed to save scraping config:', err));
}

document.getElementById('scrape-btn').addEventListener('click', () => {
    const daysInput = document.getElementById('time-horizon-days');
    const days = parseInt(daysInput ? daysInput.value : '1', 10);
    const scrapeBtn = document.getElementById('scrape-btn');
    const statusDiv = document.getElementById('scrape-status');
    const evalCheckbox = document.getElementById('evaluate-after-scrape');
    autoEvaluateAfterScrape = !!(evalCheckbox && evalCheckbox.checked);
    
    scrapeBtn.disabled = true;
    statusDiv.className = 'status-display running';
    statusDiv.textContent = 'Launching scraping...';
    
    fetch('/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: days, destinations: scrapingDestinations })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusDiv.textContent = 'Scraping in progress...';
            startScrapingPolling();
        } else {
            statusDiv.className = 'status-display error';
            statusDiv.textContent = `Error: ${data.message || 'Unknown error'}`;
            scrapeBtn.disabled = false;
        }
    })
    .catch(error => {
        statusDiv.className = 'status-display error';
        statusDiv.textContent = `Error: ${error.message}`;
        scrapeBtn.disabled = false;
    });
});

function startScrapingPolling() {
    if (scrapingInterval) clearInterval(scrapingInterval);
    
    scrapingInterval = setInterval(() => {
        fetch('/scrape/status')
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('scrape-status');
                const scrapeBtn = document.getElementById('scrape-btn');
                
                if (data.status === 'running') {
                    statusDiv.className = 'status-display running';
                    statusDiv.textContent = 'Scraping in progress...';
                } else if (data.status === 'completed') {
                    clearInterval(scrapingInterval);
                    statusDiv.className = 'status-display completed';
                    statusDiv.textContent = `Scraping completed! ${data.new_jobs_count} new jobs added.`;
                    scrapeBtn.disabled = false;

                    // Trigger latest-first review automatically if opted-in
                    if (autoEvaluateAfterScrape && data.new_jobs_count > 0) {
                        // Switch to review tab to show progress
                        document.querySelector('[data-tab="review"]').click();
                        
                        const reviewBtn = document.getElementById('review-btn');
                        const reviewStatus = document.getElementById('review-status');
                        const progressContainer = document.getElementById('review-progress');
                        reviewBtn.disabled = true;
                        reviewStatus.className = 'status-display running';
                        reviewStatus.textContent = 'Launching review...';
                        progressContainer.style.display = 'block';

                        fetch('/review/latest', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ count: data.new_jobs_count })
                        })
                        .then(response => response.json())
                        .then(resp => {
                            if (resp.success) {
                                reviewStatus.textContent = 'Review in progress...';
                                startReviewPolling();
                            } else {
                                reviewStatus.className = 'status-display error';
                                reviewStatus.textContent = `Error: ${resp.message || 'Unknown error'}`;
                                reviewBtn.disabled = false;
                                progressContainer.style.display = 'none';
                            }
                        })
                        .catch(error => {
                            reviewStatus.className = 'status-display error';
                            reviewStatus.textContent = `Error: ${error.message}`;
                            reviewBtn.disabled = false;
                            progressContainer.style.display = 'none';
                        })
                        .finally(() => {
                            autoEvaluateAfterScrape = false;
                        });
                    } else {
                        autoEvaluateAfterScrape = false;
                    }
                } else if (data.status === 'error') {
                    clearInterval(scrapingInterval);
                    statusDiv.className = 'status-display error';
                    statusDiv.textContent = `Error: ${data.error || 'Unknown error'}`;
                    scrapeBtn.disabled = false;
                } else {
                    statusDiv.className = 'status-display idle';
                    statusDiv.textContent = 'Ready to scrape';
                }
            })
            .catch(error => {
                console.error('Error polling scraping status:', error);
            });
    }, 2000); // Poll every 2 seconds
}

// Update status functionality
let updateStatusInterval = null;

document.getElementById('update-status-btn').addEventListener('click', () => {
    const updateStatusBtn = document.getElementById('update-status-btn');
    const statusDiv = document.getElementById('update-status-display');
    const progressContainer = document.getElementById('update-status-progress');
    
    updateStatusBtn.disabled = true;
    statusDiv.className = 'status-display running';
    statusDiv.textContent = 'Starting status check...';
    progressContainer.style.display = 'block';
    
    fetch('/update-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusDiv.textContent = 'Checking statuses in progress...';
            startUpdateStatusPolling();
        } else {
            statusDiv.className = 'status-display error';
            statusDiv.textContent = `Error: ${data.message || 'Unknown error'}`;
            updateStatusBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    })
    .catch(error => {
        statusDiv.className = 'status-display error';
        statusDiv.textContent = `Error: ${error.message}`;
        updateStatusBtn.disabled = false;
        progressContainer.style.display = 'none';
    });
});

function startUpdateStatusPolling() {
    if (updateStatusInterval) clearInterval(updateStatusInterval);
    
    updateStatusInterval = setInterval(() => {
        fetch('/update-status/status')
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('update-status-display');
                const updateStatusBtn = document.getElementById('update-status-btn');
                const progressBar = document.getElementById('update-status-progress-bar');
                const progressText = document.getElementById('update-status-progress-text');
                const progressContainer = document.getElementById('update-status-progress');
                
                if (data.status === 'running') {
                    statusDiv.className = 'status-display running';
                    statusDiv.textContent = 'Checking job statuses...';
                    progressContainer.style.display = 'block';
                    
                    const percentage = data.total > 0 ? (data.current / data.total) * 100 : 0;
                    progressBar.style.width = `${percentage}%`;
                    progressText.textContent = `${data.current} / ${data.total}`;
                } else if (data.status === 'completed') {
                    clearInterval(updateStatusInterval);
                    statusDiv.className = 'status-display completed';
                    statusDiv.textContent = `Status check completed! ${data.jobs_updated_count} jobs updated to 'Closed'.`;
                    progressBar.style.width = '100%';
                    progressText.textContent = `${data.total} / ${data.total}`;
                    updateStatusBtn.disabled = false;
                    
                    // Refresh job list to reflect status changes
                    refreshJobList();
                } else if (data.status === 'error') {
                    clearInterval(updateStatusInterval);
                    statusDiv.className = 'status-display error';
                    statusDiv.textContent = `Error: ${data.error || 'Unknown error'}`;
                    updateStatusBtn.disabled = false;
                    progressContainer.style.display = 'none';
                } else {
                    statusDiv.className = 'status-display idle';
                    statusDiv.textContent = 'Ready to check statuses';
                    progressContainer.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error polling update status:', error);
            });
    }, 2000); // Poll every 2 seconds
}

// Review functionality
let reviewInterval = null;

document.getElementById('review-btn').addEventListener('click', () => {
    const count = parseInt(document.getElementById('review-count').value);
    const reviewBtn = document.getElementById('review-btn');
    const statusDiv = document.getElementById('review-status');
    const progressContainer = document.getElementById('review-progress');
    
    if (count < 1) {
        alert('Please enter a valid number of reviews (minimum 1)');
        return;
    }
    
    reviewBtn.disabled = true;
    statusDiv.className = 'status-display running';
    statusDiv.textContent = 'Launching review...';
    progressContainer.style.display = 'block';
    
    fetch('/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: count })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusDiv.textContent = 'Review in progress...';
            startReviewPolling();
        } else {
            statusDiv.className = 'status-display error';
            statusDiv.textContent = `Error: ${data.message || 'Unknown error'}`;
            reviewBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    })
    .catch(error => {
        statusDiv.className = 'status-display error';
        statusDiv.textContent = `Error: ${error.message}`;
        reviewBtn.disabled = false;
        progressContainer.style.display = 'none';
    });
});

function startReviewPolling() {
    if (reviewInterval) clearInterval(reviewInterval);
    
    reviewInterval = setInterval(() => {
        fetch('/review/status')
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('review-status');
                const reviewBtn = document.getElementById('review-btn');
                const progressBar = document.getElementById('review-progress-bar');
                const progressText = document.getElementById('review-progress-text');
                const progressContainer = document.getElementById('review-progress');
                
                if (data.status === 'running') {
                    statusDiv.className = 'status-display running';
                    statusDiv.textContent = 'Review in progress...';
                    progressContainer.style.display = 'block';
                    
                    const percentage = data.total > 0 ? (data.current / data.total) * 100 : 0;
                    progressBar.style.width = `${percentage}%`;
                    progressText.textContent = `${data.current} / ${data.total}`;
                } else if (data.status === 'completed') {
                    clearInterval(reviewInterval);
                    statusDiv.className = 'status-display completed';
                    statusDiv.textContent = `Review completed! ${data.total} jobs reviewed.`;
                    progressBar.style.width = '100%';
                    progressText.textContent = `${data.total} / ${data.total}`;
                    reviewBtn.disabled = false;
                    
                    // Refresh job list
                    refreshJobList();
                } else if (data.status === 'error') {
                    clearInterval(reviewInterval);
                    statusDiv.className = 'status-display error';
                    statusDiv.textContent = `Error: ${data.error || 'Unknown error'}`;
                    reviewBtn.disabled = false;
                    progressContainer.style.display = 'none';
                } else {
                    statusDiv.className = 'status-display idle';
                    statusDiv.textContent = 'Ready to review';
                    progressContainer.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error polling review status:', error);
            });
    }, 2000); // Poll every 2 seconds
}

function refreshJobList() {
    fetch('/refresh-jobs')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the jobs data
                Object.assign(jobsData, data.jobs);
                
                // Update the sidebar
                const jobList = document.getElementById('job-list');
                jobList.innerHTML = '';
                
                data.sidebar_jobs.forEach(job => {
                    const jobItem = document.createElement('div');
                    jobItem.className = 'job-item';
                    jobItem.dataset.jobId = job.id;
                    
                    const h4 = document.createElement('h4');
                    h4.textContent = `${job.title || 'N/A'} (Score: ${job.score !== null ? job.score : 'N/A'})`;
                    
                    const p = document.createElement('p');
                    p.textContent = `${job.company || 'N/A'} - ${job.location || 'N/A'}`;
                    
                    jobItem.appendChild(h4);
                    jobItem.appendChild(p);
                    
                    jobItem.addEventListener('click', () => {
                        displayJobDetails(job.id);
                        document.querySelectorAll('.job-item').forEach(i => i.classList.remove('selected'));
                        jobItem.classList.add('selected');
                    });
                    
                    jobList.appendChild(jobItem);
                });
                
                // Update review count info
                if (data.review_count_info) {
                    const countInfoDiv = document.getElementById('review-count-info');
                    if (countInfoDiv) {
                        countInfoDiv.textContent = `À review: ${data.review_count_info.unreviewed_count} / ${data.review_count_info.total_open_count} (${data.review_count_info.percentage}%)`;
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error refreshing job list:', error);
        });
}

function displayJobDetails(jobId) {
    document.getElementById('placeholder').style.display = 'none';
    const contentDiv = document.getElementById('job-details');
    contentDiv.style.display = 'flex';
    contentDiv.style.flexDirection = 'column';
    contentDiv.style.height = '100%';
    
    const jobData = jobsData.find(j => j.id == jobId);
    if (!jobData) {
        contentDiv.innerHTML = '<h2>Error: Job not found</h2>';
        return;
    }

    // Render with header and scrollable content separated
    contentDiv.innerHTML = `
        <div class="job-header">
            <div class="job-header-left">
                <h1>${ jobData.title || 'N/A' }</h1>
                <h2>${ jobData.company || 'N/A' } - ${ jobData.location || 'N/A' }</h2>
                <p><a href="${ jobData.job_link || '#' }" target="_blank">View Original Job Post</a></p>
            </div>
            <div class="job-header-right">
                <button id="interested-btn" class="status-btn interested-btn" data-job-id="${jobId}"></button>
                <button id="not-interested-btn" class="status-btn not-interested-btn" data-job-id="${jobId}"></button>
                <button id="apply-btn" class="status-btn apply-btn" data-job-id="${jobId}">Apply</button>
            </div>
        </div>
        <div class="job-content-scrollable">
            <div class="info">
                <h3>Review</h3>
                <p><b>ID:</b> ${ jobData.id }</p>
                <p><b>Score:</b> ${ jobData.score !== null ? jobData.score : 'N/A' }</p>
                <p><b>Preferred Pitch:</b> ${ jobData.preferred_pitch || 'N/A' }</p>
            </div>
            <h2>Evaluation Grid</h2>
            ${formatEvaluationGrid(jobData.evaluation_grid)}
            <h2>Synthesis and Decision</h2>
            <div class="job-description-content">${ jobData['synthesis_and_decision'] || 'Not available.' }</div>
            <h3>Full Job Description</h3>
            <div id="live-description-container"><div id="loader">Fetching live details...</div></div>
        </div>
    `;

    document.getElementById('apply-btn').addEventListener('click', () => applyForJob(jobId));
    updateStatusButtons(jobId);

    // Fetch and render live description
    fetch(`/job/${jobId}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('live-description-container');
            if (data.description) {
                container.innerHTML = `<div class="job-description-content">${data.description}</div>`;
            } else {
                container.innerHTML = `<pre>Could not retrieve live job description. Stored link: <a href="${jobData.job_link}" target="_blank">${jobData.job_link}</a></pre>`;
            }
        })
        .catch(error => {
            console.error('Error fetching job details:', error);
            const container = document.getElementById('live-description-container');
            container.innerHTML = '<pre>Error fetching live details.</pre>';
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

function updateStatusButtons(jobId) {
    const interestedBtn = document.getElementById('interested-btn');
    const notInterestedBtn = document.getElementById('not-interested-btn');
    const jobData = jobsData.find(j => j.id == jobId);

    if (jobData.status) {
        if (jobData.status.applied) {
            interestedBtn.textContent = `Interested (${jobData.status.date})`;
            interestedBtn.disabled = true;
            notInterestedBtn.style.display = 'none';
        } else {
            notInterestedBtn.textContent = `Not Interested (${jobData.status.date})`;
            notInterestedBtn.disabled = true;
            interestedBtn.style.display = 'none';
        }
    } else {
        interestedBtn.textContent = 'Interested';
        interestedBtn.disabled = false;
        interestedBtn.style.display = 'inline-block';
        notInterestedBtn.textContent = 'Not Interested';
        notInterestedBtn.disabled = false;
        notInterestedBtn.style.display = 'inline-block';

        interestedBtn.onclick = () => updateJobStatus(jobId, true);
        notInterestedBtn.onclick = () => updateJobStatus(jobId, false);
    }
}

function updateJobStatus(jobId, isInterested) {
    fetch(`/status/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ applied: isInterested })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove item from sidebar
            const jobItem = document.querySelector(`.job-item[data-job-id='${jobId}']`);
            if (jobItem) {
                jobItem.remove();
            }
            // Hide details and show placeholder
            document.getElementById('job-details').style.display = 'none';
            document.getElementById('placeholder').style.display = 'block';
            // Refresh job list to update the count
            refreshJobList();
        }
    });
}

function applyForJob(jobId) {
    const applyBtn = document.getElementById('apply-btn');
    applyBtn.textContent = 'Loading...';
    applyBtn.disabled = true;

    // Simply redirect to the customizer interface URL
    window.location.href = `/customizer/apply/${jobId}`;
}
