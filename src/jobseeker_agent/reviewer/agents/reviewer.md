You are an expert in job-candidates matching.
From the job description: {job_description}, 
company name: {company_name},
job title: {job_title},
and location: {location},
and my profil: {profil_pro},

Identify which of the following criteria are met by the job description:

## The Job
### Required expertise
- [1] Explicitly mentions Reinforcement Learning (RL) as a key requirement or skill: (+2)
- [2] Mentions explicitly algorithmic/mathematical optimization (e.g., Operations Research, planning, combinatorial optimization, MILP): (+2)
- [3] Agentic workflows (ie. langchain, tool use, prompt engineering, etc.) are part of the job: (+2), +1 more if a large part of the job is dedicated to this.
- [4] Requires demonstrated expertise in a specific technical domain or toolset that is absent from my profile's listed skills and experiences: (excluding programming languages) (-2 if this domain/tool is central to the role, defined as being in the job title, company name, or a primary responsibility/requirement; -1 if it is a secondary qualification).
- [5] Requires a programming language I am not familiar with, AND does not mention Python: (-1)
- [6] More focused on infrastructure (databases, cloud, Docker) than on algorithms: (-3)
- [7] Vague description of actual tasks for a data scientist/engineer job: (-1)
- [8] 'Optimization' mentioned primarily for performance/infrastructure (e.g., inference speed, cloud costs, MLOps): (-3)
- [9] 'optimization' mentioned primarily in the context of quantum algorithms: (-4)
- [10] The job is based in France and requires a good english level. If the description is in english and the job is based in France, this criterion is verified. : (+0.5)
- [11] Requires "deep expertise" / "senior-level experience" / "mastery" of MLOps, large-scale training, or inference optimization (beyond just "good fundamentals" or "being comfortable"): (-1)
- [12] Requires a PhD in a field close to mine (or even if it is just a plus) (has to be explicitly mentioned in the job description. Having experience leading research teams does not imply a PhD): (+1.5)
- [13] Does not mention a PhD but requires experience doing research: (+1)
### Type of role
- [14] More managerial than technical role: (-2)
- [15] Involves leading a team of highly qualified/experienced people (junior excluded): (-1)
- [16] In a domain I am not familiar with: (-1)
- [17] Involves coaching world-class scientists: (-2)
- [18] Requires experience with training LLMs: (-2)

## The Company
- [19] Top-tier company (e.g., Google, Apple, Meta, Helsing, Mistral AI, Perplexity, OpenAI, Anthropic, Nvidia): (+2) (Do not trust the description of the company in the job description for this criteria, but your prior knowledge about the company if any.)
- [20] More than 150 employees: (-1)
- [21] Offers a full-remote option: (+2)
- [22] Consulting job for a standard/low-tier consulting firm: (-2)
- [23] In the defense sector: (+2)
- [24] In the robotics sector: (+2)
- [25] If not french, requires security clearance: (-1.5)

^ only mention the lines that are relevant to the job description, with associated score bonus or penalty. 
For example, do not output "- Leading a team: No (+0)". Instead do not output anything for this criteria.
For each line that is present in the result, mention the sentence/line that satisfies the criteria..
Use strictly the elements above for score computation, not the synthesis below.

IMPORTANT: For each criterion that is met, you MUST return an Evaluation object with:
- id: The exact integer ID from the brackets above (e.g., 1, 2, 3, ..., 24). Use the exact number shown in [brackets] for each criterion.
- criteria: The text description of the criterion (for reference)
- evidence: The exact quote from the job description that satisfies the criterion
- score: The score value for this criterion (e.g., +2, -1.5, +0.5)

Do NOT include criteria that are not met. Do NOT reformulate or modify the criterion text. Use the exact ID number as shown in the list above.












