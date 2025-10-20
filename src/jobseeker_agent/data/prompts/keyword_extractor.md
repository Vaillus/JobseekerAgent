You are an expert in job-candidates matching and in resume optimization.

# Input data
## Job description
{job_description}

## Candidate profile
{profil_pro}

## Candidate resume
{cv_template}

# Task
From this data, first identify the keywords and required skills and domains that are present in the job description, and output them in decreasing order of relevance for the job.

In each field's list, group keywords that are related to the same domain in sublists.
eg: instead of [
    "godot",
    "godot game engine",
    "simulator",
    "camera calibration",
    "computer vision",
    "opencv",
    "yolov8",
    "optical flow",
    "publications"
]
you should have a dictionary with the following structure:
    "simulation": ["godot", "godot game engine", "simulator"],
    "computer vision": ["camera calibration", "computer vision", "opencv", "yolov8", "optical flow"]

### Keyword Extraction Rules:
1.  **Prioritize Transferable Technical Skills:** Focus exclusively on skills, technologies, frameworks, and concepts that are transferable across different companies and industries.
    - **INCLUDE**: Programming languages (`Python`, `SQL`), specific libraries/frameworks (`LangChain`, `TensorFlow`), core concepts (`agents IA`, `RAG`, `scalability`, `APIs`), and methodologies (`agile`).
    - **EXCLUDE**: Industry-specific business jargon. For example, in this job, extract `Python` and `agents IA`, but completely ignore terms like `marketplace`, `dropship`, `retail media`, `B2C`, etc. These are irrelevant for the candidate's skill evaluation.

2.  **Extract Core Responsibilities:** Identify the key actions and tasks the person will perform (e.g., "développement d’agents IA", "automatiser des workflows", "intégrer des systèmes").

3.  **Filter Soft Skills:**
    - **INCLUDE**: Only concrete, action-oriented soft skills that can be demonstrated (e.g., "partager son travail en conférence", "rédiger des articles", "collaborer avec les équipes produit").
    - **EXCLUDE**: Vague, generic soft skills and business buzzwords. Ignore terms like `pragmatique`, `data-driven`, `orienté métier`, `ownership`, `fast-paced`, `impact`.

4.  **Ignore Boilerplate:** Discard all information about the company's mission, culture descriptions, diversity statements, and logistics (e.g., "Mirakl est le leader...", "basé sur Paris...").

# Observations
- Proficiency in spanish/french is always good to mention.
- If the job is about ML/DL, experience in "optimization" and "operations research" are always good to mention, they are at the core of my phd.
- do not mention overly general words such "pragmatic tradeoffs", "impact", ""adoption of new techniques", "remote work", "fast-paced" ""continual improvement" as they are irrelevant for further resume modifications.
- years of experience are not relevant here.
- FCAS project is always good to mention because it is a big european project.
