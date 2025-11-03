"""
Serveur Flask pour gérer la sauvegarde de la ground truth.
Lance une interface web pour valider les critères et sauvegarde directement dans le projet.
"""

from flask import Flask, render_template_string, jsonify, request
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

from jobseeker_agent.reviewer.evaluation.batch_review import load_batch_results
from jobseeker_agent.utils.paths import get_data_path, load_full_job


# Liste des critères avec leurs descriptions (ordre original)
CRITERIA_LIST = [
    {"id": 1, "description": "Explicitly mentions Reinforcement Learning (RL) as a key requirement or skill: (+2)"},
    {"id": 2, "description": "Mentions explicitly algorithmic/mathematical optimization (e.g., Operations Research, planning, combinatorial optimization, MILP): (+2)"},
    {"id": 3, "description": "Agentic workflows (ie. langchain, tool use, prompt engineering, etc.) are part of the job: (+2), +1 more if a large part of the job is dedicated to this."},
    {"id": 4, "description": "Requires demonstrated expertise in a specific technical domain or toolset that is absent from my profile's listed skills and experiences: (-2 if this domain/tool is central to the role, defined as being in the job title, company name, or a primary responsibility/requirement; -1 if it is a secondary qualification)."},
    {"id": 5, "description": "Requires a programming language I am not familiar with, AND does not mention Python: (-1)"},
    {"id": 6, "description": "More focused on infrastructure (databases, cloud, Docker) than on algorithms: (-3)"},
    {"id": 7, "description": "Vague description of actual tasks for a data scientist/engineer job: (-1)"},
    {"id": 8, "description": "'Optimization' mentioned primarily for performance/infrastructure (e.g., inference speed, cloud costs, MLOps): (-3)"},
    {"id": 9, "description": "'optimization' mentioned primarily in the context of quantum algorithms: (-4)"},
    {"id": 10, "description": "The job is based in France and requires a good english level. If the description is in english and the job is based in France, this criterion is verified. : (+0.5)"},
    {"id": 11, "description": "Requires \"deep expertise\" / \"senior-level experience\" / \"mastery\" of MLOps, large-scale training, or inference optimization (beyond just \"good fundamentals\" or \"being comfortable\"): (-1)"},
    {"id": 12, "description": "Requires a PhD in a field close to mine (or even if it is just a plus) (has to be explicitly mentioned in the job description. Having experience leading research teams does not imply a PhD): (+1.5)"},
    {"id": 13, "description": "Does not mention a PhD but requires experience doing research: (+1)"},
    {"id": 14, "description": "More managerial than technical role: (-2)"},
    {"id": 15, "description": "Involves leading a team of highly qualified/experienced people (junior excluded): (-1)"},
    {"id": 16, "description": "In a domain I am not familiar with: (-1)"},
    {"id": 17, "description": "Involves coaching world-class scientists: (-2)"},
    {"id": 18, "description": "Top-tier company (e.g., Google, Apple, Meta, Helsing, Mistral AI, Perplexity, OpenAI, Anthropic, Nvidia): (+2) (Do not trust the description of the company in the job description for this criteria, but your prior knowledge about the company if any.)"},
    {"id": 19, "description": "More than 150 employees: (-1)"},
    {"id": 20, "description": "Offers a full-remote option: (+2)"},
    {"id": 21, "description": "Consulting job for a standard/low-tier consulting firm: (-2)"},
    {"id": 22, "description": "In the defense sector: (+2)"},
    {"id": 23, "description": "In the robotics sector: (+2)"},
    {"id": 24, "description": "If not french, requires security clearance: (-1.5)"},
]

CRITERIA_MAP = {c["id"]: c["description"] for c in CRITERIA_LIST}


def aggregate_detections(reviews: List[Dict]) -> Dict[int, Dict[str, List[Dict]]]:
    """Agrège les détections de critères par job."""
    aggregations = defaultdict(lambda: defaultdict(lambda: {
        'count': 0,
        'detected_by': [],
        'evidences': []
    }))
    
    for review in reviews:
        job_id = review['job_id']
        config_name = review['config_name']
        review_result = review.get('review_result', {})
        
        if review_result and 'evaluation_grid' in review_result:
            for criterion in review_result['evaluation_grid']:
                criterion_id = criterion['id']
                evidence = criterion.get('evidence', '')
                
                aggregations[job_id][criterion_id]['count'] += 1
                aggregations[job_id][criterion_id]['detected_by'].append(config_name)
                aggregations[job_id][criterion_id]['evidences'].append(evidence)
    
    return dict(aggregations)


app = Flask(__name__)

# Variables globales pour stocker l'état
GENERATION_ID = None
JOB_DATA = None


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ground Truth Validation - Generation {{ generation_id }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .progress {
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
        }
        
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            min-height: calc(100vh - 200px);
        }
        
        .panel {
            padding: 30px;
            overflow-y: auto;
            max-height: calc(100vh - 200px);
        }
        
        .job-desc-panel {
            background-color: #fafafa;
            border-right: 1px solid #e0e0e0;
        }
        
        .criteria-panel {
            background-color: white;
        }
        
        .job-title {
            font-size: 22px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }
        
        .job-meta {
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .job-description {
            font-size: 14px;
            line-height: 1.7;
            color: #444;
            white-space: pre-wrap;
            text-align: justify;
        }
        
        .criteria-section {
            margin-bottom: 25px;
        }
        
        .criteria-section h3 {
            font-size: 14px;
            text-transform: uppercase;
            color: #999;
            margin-bottom: 15px;
            letter-spacing: 0.5px;
        }
        
        .criterion-item {
            margin-bottom: 12px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }
        
        .criterion-item:hover {
            border-color: #667eea;
            background-color: #f0f0ff;
        }
        
        .criterion-item.selected {
            border-color: #667eea;
            background-color: #eef2ff;
        }
        
        .criterion-checkbox {
            display: none;
        }
        
        .criterion-header {
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        
        .criterion-number {
            flex-shrink: 0;
            width: 32px;
            height: 32px;
            background: #667eea;
            color: white;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
        }
        
        .criterion-item.selected .criterion-number {
            background: #10b981;
        }
        
        .criterion-text {
            flex: 1;
            font-size: 13px;
            color: #444;
            line-height: 1.5;
        }
        
        .criterion-count {
            margin-top: 8px;
            font-size: 11px;
            color: #888;
            padding: 4px 8px;
            background: #f0f0f0;
            border-radius: 4px;
            display: inline-block;
        }
        
        .criterion-count.high {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .criterion-count.medium {
            background: #fef3c7;
            color: #92400e;
        }
        
        .criterion-count.low {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .detected-by {
            margin-top: 8px;
            font-size: 11px;
            color: #666;
        }
        
        .detected-by .model-tag {
            display: inline-block;
            padding: 2px 6px;
            background: #e0e0e0;
            border-radius: 3px;
            margin-right: 4px;
            margin-top: 4px;
        }
        
        .detected-by .model-tag.gpt-4 {
            background: #e3f2fd;
            color: #1565c0;
        }
        
        .detected-by .model-tag.gpt-5 {
            background: #f3e5f5;
            color: #6a1b9a;
        }
        
        .actions {
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 12px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .btn-next {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-next:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-next:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .stats {
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            font-size: 13px;
        }
        
        .stats-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        
        .stats-value {
            font-weight: 600;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Ground Truth Validation</h1>
            <div class="progress" id="progress">Job 1 of {{ job_count }}</div>
        </div>
        
        <div class="content" id="content">
        </div>
        
        <div class="actions">
            <button class="btn btn-next" id="btnNext">Valider & Suivant →</button>
        </div>
    </div>
    
    <script>
        const jobData = {{ job_data | tojson }};
        const criteriaMap = {{ criteria_map | tojson }};
        const allCriteriaIds = {{ all_criteria_ids | tojson }};
        
        let currentJobIndex = 0;
        const selectedCriteria = {};
        
        function getCurrentJobId() {
            return jobData.jobs[currentJobIndex];
        }
        
        function updateProgress() {
            const progress = document.getElementById('progress');
            progress.textContent = `Job ${currentJobIndex + 1} of ${jobData.jobs.length}`;
        }
        
        function getCriteriaSorted(jobId) {
            const aggregations = jobData.aggregations[jobId] || {};
            const criteriaWithCounts = Object.entries(aggregations).map(([id, info]) => [
                parseInt(id),
                info.count
            ]);
            criteriaWithCounts.sort((a, b) => {
                if (b[1] !== a[1]) return b[1] - a[1];
                return a[0] - b[0];
            });
            return criteriaWithCounts.map(([id]) => id);
        }
        
        function renderJob() {
            const jobId = getCurrentJobId();
            const aggregations = jobData.aggregations[jobId] || {};
            const jobInfo = jobData.jobs_map[jobId];
            const sortedCriteriaIds = getCriteriaSorted(jobId);
            
            // Rendre la description du job
            const jobDescHtml = `
                <div class="job-desc-panel">
                    <div class="job-title">${jobInfo.title || 'Unknown'}</div>
                    <div class="job-meta">
                        <strong>${jobInfo.company || 'Unknown Company'}</strong> • ${jobInfo.location || 'Unknown Location'}
                    </div>
                    <div class="job-description">${(jobInfo.description || 'No description available').slice(0, 5000)}${jobInfo.description && jobInfo.description.length > 5000 ? '...' : ''}</div>
                </div>
            `;
            
            // Rendre les critères
            let criteriaHtml = `
                <div class="criteria-panel">
                    <div class="stats">
                        <div class="stats-row">
                            <span>Critères détectés:</span>
                            <span class="stats-value">${Object.keys(aggregations).length}</span>
                        </div>
                        <div class="stats-row">
                            <span>Vos sélections:</span>
                            <span class="stats-value" id="selectedCount">0</span>
                        </div>
                    </div>
            `;
            
            // Critères détectés par les LLMs (triés)
            const detectedIds = new Set(Object.keys(aggregations).map(Number));
            
            for (const criterionId of sortedCriteriaIds) {
                const info = aggregations[criterionId];
                const isSelected = selectedCriteria[jobId]?.has(criterionId) || false;
                const countClass = info.count >= 3 ? 'high' : info.count === 2 ? 'medium' : 'low';
                
                criteriaHtml += `
                    <div class="criterion-item ${isSelected ? 'selected' : ''}" onclick="toggleCriterion(${criterionId})">
                        <div class="criterion-header">
                            <div class="criterion-number">${criterionId}</div>
                            <div class="criterion-text">${criteriaMap[criterionId]}</div>
                        </div>
                        <div class="criterion-count ${countClass}">
                            ${info.count} LLM(s) détecté • ${info.detected_by.join(', ')}
                        </div>
                    </div>
                `;
            }
            
            // Ajouter les critères non détectés à la fin
            for (const criterionId of allCriteriaIds) {
                if (!detectedIds.has(criterionId)) {
                    const isSelected = selectedCriteria[jobId]?.has(criterionId) || false;
                    criteriaHtml += `
                        <div class="criterion-item ${isSelected ? 'selected' : ''}" onclick="toggleCriterion(${criterionId})">
                            <div class="criterion-header">
                                <div class="criterion-number" style="background: #ccc;">${criterionId}</div>
                                <div class="criterion-text">${criteriaMap[criterionId]}</div>
                            </div>
                            <div class="criterion-count">Non détecté</div>
                        </div>
                    `;
                }
            }
            
            criteriaHtml += '</div>';
            
            document.getElementById('content').innerHTML = jobDescHtml + criteriaHtml;
            updateSelectedCount();
            updateProgress();
        }
        
        function toggleCriterion(criterionId) {
            const jobId = getCurrentJobId();
            if (!selectedCriteria[jobId]) {
                selectedCriteria[jobId] = new Set();
            }
            
            if (selectedCriteria[jobId].has(criterionId)) {
                selectedCriteria[jobId].delete(criterionId);
            } else {
                selectedCriteria[jobId].add(criterionId);
            }
            
            renderJob();
        }
        
        function updateSelectedCount() {
            const jobId = getCurrentJobId();
            const count = selectedCriteria[jobId]?.size || 0;
            document.getElementById('selectedCount').textContent = count;
        }
        
        async function saveAndNext() {
            // Sauvegarder la ground truth pour ce job
            const jobId = getCurrentJobId();
            const validatedIds = Array.from(selectedCriteria[jobId] || []);
            
            console.log('Validated for job', jobId, ':', validatedIds);
            
            // Passer au job suivant
            currentJobIndex++;
            
            if (currentJobIndex >= jobData.jobs.length) {
                // Tous les jobs sont validés - sauvegarder toutes les ground truths
                await saveAllGroundTruth();
                alert('✅ Tous les jobs ont été validés! La ground truth a été sauvegardée.');
                return;
            }
            
            renderJob();
        }
        
        async function saveAllGroundTruth() {
            // Convertir selectedCriteria en format liste plate
            const groundTruth = [];
            for (const jobId of jobData.jobs) {
                const validatedIds = Array.from(selectedCriteria[jobId] || []);
                groundTruth.push({
                    job_id: jobId,
                    validated_criteria: validatedIds
                });
            }
            
            // Envoyer au serveur pour sauvegarde
            const response = await fetch('/save_ground_truth', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    generation_id: jobData.generation_id,
                    ground_truth: groundTruth
                })
            });
            
            const result = await response.json();
            console.log('Ground truth sauvegardée:', result);
        }
        
        document.getElementById('btnNext').addEventListener('click', saveAndNext);
        
        // Initialiser
        renderJob();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Page principale avec l'interface de validation."""
    return render_template_string(
        HTML_TEMPLATE,
        generation_id=GENERATION_ID,
        job_count=len(JOB_DATA['jobs']),
        job_data=JOB_DATA,
        criteria_map=CRITERIA_MAP,
        all_criteria_ids=[c['id'] for c in CRITERIA_LIST]
    )


@app.route('/save_ground_truth', methods=['POST'])
def save_ground_truth():
    """Endpoint pour sauvegarder la ground truth."""
    data = request.json
    generation_id = data['generation_id']
    ground_truth = data['ground_truth']
    
    # Sauvegarder dans le dossier du projet
    output_path = get_data_path() / "reviewer" / "tests" / str(generation_id) / "ground_truth.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Ground truth sauvegardée: {output_path}")
    
    return jsonify({
        'success': True,
        'message': f'Ground truth saved to {output_path}',
        'path': str(output_path)
    })


def launch_validation_interface(generation_id: int, port: int = 5000):
    """Lance l'interface de validation pour une génération donnée."""
    global GENERATION_ID, JOB_DATA
    
    GENERATION_ID = generation_id
    
    print("=" * 60)
    print(f"🎨 Chargement des données - Generation {generation_id}")
    print("=" * 60)
    
    # Charger les reviews
    reviews = load_batch_results(generation_id)
    if not reviews:
        print(f"❌ Aucun résultat trouvé pour generation {generation_id}")
        return
    
    # Extraire les job_ids uniques
    job_ids = sorted(set(review['job_id'] for review in reviews))
    print(f"📋 {len(job_ids)} jobs à valider")
    
    # Charger les jobs complets avec descriptions
    print("📥 Chargement des descriptions des jobs...")
    jobs_map = {}
    for job_id in job_ids:
        try:
            job = load_full_job(job_id)
            jobs_map[job_id] = job
        except Exception as e:
            print(f"⚠️  Erreur chargement job {job_id}: {e}")
            jobs_map[job_id] = {
                'id': job_id,
                'title': 'Unknown',
                'company': 'Unknown',
                'location': 'Unknown',
                'description': 'Could not load description'
            }
    
    print(f"✅ {len(jobs_map)} jobs chargés")
    
    # Agréger les détections
    aggregations_by_job = aggregate_detections(reviews)
    
    JOB_DATA = {
        'jobs': job_ids,
        'aggregations': aggregations_by_job,
        'jobs_map': jobs_map,
        'generation_id': generation_id
    }
    
    print()
    print("=" * 60)
    print(f"🚀 Lancement du serveur sur http://localhost:{port}")
    print("=" * 60)
    print()
    print("📝 Instructions:")
    print(f"   1. Ouvrez http://localhost:{port} dans votre navigateur")
    print("   2. Validez les critères pour chaque job")
    print("   3. Cliquez sur 'Valider & Suivant' pour passer au job suivant")
    print("   4. La ground truth sera sauvegardée automatiquement dans:")
    output_path = get_data_path() / "reviewer" / "tests" / str(generation_id) / "ground_truth.json"
    print(f"      {output_path}")
    print()
    
    app.run(debug=True, port=port)


def main():
    """Point d'entrée principal."""
    generation_id = 6
    launch_validation_interface(generation_id, port=5000)


if __name__ == "__main__":
    main()

