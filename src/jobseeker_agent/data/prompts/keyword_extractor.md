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

# Observations
- Proficiency in spanish/french is always good to mention.
- If the job is about ML/DL, experience in "optimization" and "operations research" are always good to mention, they are at the core of my phd.
- do not mention overly general words such "pragmatic tradeoffs", "impact", ""adoption of new techniques", "remote work", "fast-paced" ""continual improvement" as they are irrelevant for further resume modifications.
- years of experience are not relevant here.
- FCAS project is always good to mention because it is a big european project.
