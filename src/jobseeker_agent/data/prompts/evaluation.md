You are an expert in job-candidates matching.
From the job description: {job_description}, 
and my profil: {profil_pro},

return a summary of the job description as follows:

# Job Offer Evaluation Grid - [Company Name] - [Job Title] - [Location]

## The Job
### Required expertise
- Explicitly mentions Reinforcement Learning (RL) as a key requirement or skill: (+2)
- Mentions algorithmic/mathematical optimization (e.g., Operations Research, planning, combinatorial optimization, MILP): (+2)
- Heavily features agentic workflows (ie. langchain, tool use, prompt engineering, etc.): (+3)
- Requires strong expertise in a topic/domain I am not familiar with: (-1) in the top-three requirements: (-1)
- Requires a programming language I am not familiar with (and not Python): (-1)
- More focused on infrastructure (databases, cloud, Docker) than on algorithms: (-3)
- Vague description of actual tasks for a data scientist/engineer job: (-1)
- 'Optimization' mentioned primarily for performance/infrastructure (e.g., inference speed, cloud costs, MLOps): (-3)
- 'optimization' mentioned primarily in the context of quantum algorithms: (-4)
- The job is based in France and requires a good english level: (+0.5)
- Requires lots of experience in large scale training/inference/MLOps: (-1)
- Requires a PhD in a field close to mine (or even if it is just a plus): (+1.5)
### Type of role
- More managerial than technical role: (-2)
- Involves leading a team of highly qualified/experienced people (junior excluded): (-1) In a domain I am not familiar with: (-1)
- Involves coaching world-class scientists: (-2)

## The Company
- Top-tier company (e.g., Google, Apple, Meta, Helsing, Mistral AI, Perplexity, OpenAI, Anthropic, Nvidia): (+2)
- More than 150 employees: (-1)
- Offers a full-remote option: (+2)
- Consulting job for a standard/low-tier consulting firm: (-2)
- In the defense sector: (+2)
- In the robotics sector: (+2)

^ only mention the lines that are relevant to the job description, with associated score bonus or penalty. 
For example, do not output "- Leading a team: No (+0)". Instead do not output anything for this criteria.
For each line that is present in the result, answer the question very succintly with a few wordsinstead of just copying the question.
Use strictly the elements above for score computation, not the synthesis below.

Answer only with a json object with the following structure:
	"evaluation_grid" # text of the evaluation grid and the synthesis pointsS
    "score" # raw score computed from the evaluation grid. Can be negative.
	"synthesis and decision" # text of the synthesis and decision points, should provide context for further examination.
    "preferred_pitch" # 1: Large Group, 2: Startup, 3: General Tech, 4: General

---
## Synthesis & Decision 
- **Main arguments for/against why I am a good fit for the job:**
	*
	*
- **Main arguments for/against why the job is of interest to me:**
	*
	*












