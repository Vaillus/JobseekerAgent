You are an expert in job-candidates matching and in resume optimization.

# Input data
## Job description
{job_description}

## Candidate profile
{profil_pro}

## Candidate resume
{resume}

# task
The task is divided into two parts.
## Part 1: Experience ranking
In my resume template, there are 4 experiences : JobseekerAgent, CameraCalibration, Thales DMS, IBM France.
Rank them in decreasing order of relevance for the job.
Also take into account the significance of that experience in my profile. For example, never put my PhD last. It is my most consequential experience in terms of time and impact.
But if one experience is strongly more relevant than my thesis, put it first.

## Part 2: Skill ranking
In the Skills section of the resume, in each field, rank the skills in decreasing order of relevance for the job.
The skills names should be strictly the same as in the resume. (e.g. ["Optimization", "Operations Research"] should not become ["Optimization (Operations Research)"] ;  and "evaluation methods" should not become "Evaluation methods (evaluation \& continuous improvement of agents)").
Keep skills in the .tex format with "\&" for the "&" character and so on.

