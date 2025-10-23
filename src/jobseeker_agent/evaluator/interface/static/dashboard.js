document.querySelectorAll('.job-item').forEach(item => {
    item.addEventListener('click', () => {
        const jobId = item.dataset.jobId;
        displayJobDetails(jobId);
        document.querySelectorAll('.job-item').forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');
    });
});

function displayJobDetails(jobId) {
    document.getElementById('placeholder').style.display = 'none';
    const contentDiv = document.getElementById('job-details');
    contentDiv.style.display = 'block';
    
    const jobData = jobsData.find(j => j.id == jobId);
    if (!jobData) {
        contentDiv.innerHTML = '<h2>Error: Job not found</h2>';
        return;
    }

    // Initial render with stored data
    contentDiv.innerHTML = `
        <h1>${ jobData.title || 'N/A' }</h1>
        <h2>${ jobData.company || 'N/A' } - ${ jobData.location || 'N/A' }</h2>
        <p><a href="${ jobData.job_link || '#' }" target="_blank">View Original Job Post</a></p>
        <hr>
        <div class="info">
            <h3>Evaluation</h3>
            <p><b>ID:</b> ${ jobData.id }</p>
            <p><b>Score:</b> ${ jobData.score !== null ? jobData.score : 'N/A' }</p>
            <p><b>Preferred Pitch:</b> ${ jobData.preferred_pitch || 'N/A' }</p>
        </div>
        <h2>Evaluation Grid</h2>
        <pre>${ jobData.evaluation_grid ? JSON.stringify(jobData.evaluation_grid, null, 2) : 'Not available.' }</pre>
        <h2>Synthesis and Decision</h2>
        <pre>${ jobData['synthesis_and_decision'] || 'Not available.' }</pre>
        <h3>Full Job Description</h3>
        <div id="live-description-container"><div id="loader">Fetching live details...</div></div>
        <div class="btn-container">
            <button id="interested-btn" class="status-btn interested-btn" data-job-id="${jobId}"></button>
            <button id="not-interested-btn" class="status-btn not-interested-btn" data-job-id="${jobId}"></button>
            <button id="apply-btn" class="status-btn" data-job-id="${jobId}">Apply</button>
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
                container.innerHTML = `<pre>${data.description}</pre>`;
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
        }
    });
}

function applyForJob(jobId) {
    const applyBtn = document.getElementById('apply-btn');
    applyBtn.textContent = 'Loading...';
    applyBtn.disabled = true;

    fetch(`/apply/${jobId}`, { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            document.getElementById('sidebar').style.display = 'none';
            const contentDiv = document.getElementById('content');
            contentDiv.innerHTML = html;
            contentDiv.style.width = '100%'; // Make content take full width

            const oldScript = document.querySelector('script[data-script-id="corrector-script"]');
            if (oldScript) {
                oldScript.remove();
            }

            const script = document.createElement('script');
            script.src = '/corrector/static/dashboard.js';
            script.dataset.scriptId = 'corrector-script';
            document.body.appendChild(script);
        })
        .catch(error => {
            console.error('Error loading corrector interface:', error);
            applyBtn.textContent = 'Error';
            applyBtn.disabled = false;
            alert('Could not load the corrector interface. Please check the console for details.');
        });
}
