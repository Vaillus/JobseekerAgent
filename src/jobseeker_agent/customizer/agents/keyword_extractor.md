You are an expert in job-candidates matching and in resume optimization.

# Input data

## Job title

{job_title}

## Job description

{job_description}

## Candidate profile

{profil_pro}

## Candidate resume

{cv_template}

# Task

From this data, first identify the keywords and required skills and domains that are present in the job description, and output them in decreasing order of relevance for the job.

## Keyword Extraction Rules:

1. **Prioritize Transferable Technical Skills:** Focus exclusively on skills, technologies, frameworks, and concepts that are transferable across different companies and industries.
   - **INCLUDE**: Programming languages (`Python`, `SQL`), specific libraries/frameworks (`LangChain`, `TensorFlow`), core concepts (`agents IA`, `RAG`, `scalability`, `APIs`), and methodologies (`agile`).
   - **EXCLUDE**: Industry-specific business jargon. For example, extract `Python` and `agents IA`, but completely ignore terms like `marketplace`, `dropship`, `retail media`, `B2C`, etc. These are irrelevant for the candidate's skill evaluation.
2. **Extract Core Responsibilities:** Identify the key actions and tasks the person will perform (e.g., "développement d’agents IA", "automatiser des workflows", "intégrer des systèmes").
3. **Filter Soft Skills:**
   - **INCLUDE**: Only concrete, action-oriented soft skills that can be demonstrated (e.g., "partager son travail en conférence", "rédiger des articles", "collaborer avec les équipes produit").
   - **EXCLUDE**: Vague, generic soft skills and business buzzwords. Ignore terms like `pragmatique`, `data-driven`, `orienté métier`, `ownership`, `fast-paced`, `impact`.
4. **Ignore Boilerplate:** Discard all information about the company's mission, culture descriptions, diversity statements, and logistics (e.g., "Mirakl est le leader...", "basé sur Paris...").
5. **Already in Skills/Technologies section**: 
   - Do NOT extract keywords that are already explicitly listed in the candidate's resume Skills/Technologies section
   - Examples to ignore: Python, PyTorch, JAX, SQL (if already visible)
6. Types of skills to ignore: 
- AWS/Azure/GCP, Kubernetes. I have experience with dockers but that's all.
- LLM finetuning.
- CI/CD
- MySQL, bigquery, snowflake, though I have experience with SQL.
- APIs
- vector search, vector databases, semantic search, RAG.
- A/B testing,
- explicit LLM providers (OpenAI, Claude, Cohere, etc.)
7. Do not extract keywords that are in my profile/resume but are not in the job description.
8. **Overly basic/universal skills & vague processes**:
   - Ignore skills that are universally expected and don't differentiate: "version control", "Git" (unless specific tool like GitLab CI is relevant)
   - Ignore vague activity descriptions without technical substance: "technical specifications", "documentation", "meetings", "real data", "working with stakeholders"

### Observations

- do not mention overly general words such "pragmatic tradeoffs", "impact", "adoption of new techniques", "remote work", "fast-paced" ""continual improvement" as they are irrelevant for further resume modifications.
- years of experience are not relevant here.
- Avoid keywords like "automatic report generation (conceptual via projects with LLM prompts)" -> just output "automatic report generation".
- Avoid grouping keywords as in "Vector databases / semantic search / RAG". Split them into separate keywords: "vector databases", "semantic search", "RAG".
- do not make groups containing only keywords that are already present in the candidate's resume. Discard them.

## Keyword grouping rules:
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

## Title suggestions rules:
Also, provide 3 suggestions for the title of the resume that are good fits for the job description and the candidate profile.
If the job title from the offer it is a valid title for the candidate, put it in the suggestions.
Do not use the word "senior" in the title.
Keep it simple, ideally 4 words maximum, down to 2.
