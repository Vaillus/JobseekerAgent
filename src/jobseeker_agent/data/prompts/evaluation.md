From the job description: {job_description}, 
and my profil: {profil_pro},

return a summary of the job description as follows:

# Job Offer Evaluation Grid - [Company Name]

## The Job
### Required expertise
- Does the job explicitly mention Reinforcement Learning (RL) as a key requirement or skill? (+2)
- Does the job mention Operations Research (OR), optimization, or planning algorithms? (+2)
- Does the job heavily feature agentic workflows (ie. langchain, tool use, prompt engineering, etc.)? (+3)
- Does the job require strong expertise in a topic I am not familiar with? (-1)
- Does the job require a programming language I am not familiar with (and not Python)? (-1)
- Is the job more focused on infrastructure (databases, cloud, Docker) than on algorithms? (-2)
- If the job is a data scientist/engineer job, is the description vague about the actual tasks? (-1)
### Type of role
- Is the role more managerial than technical? (-1)
- Is the job about leading a team of highly qualified people? (-1) In a domain I am not familiar with? (-1)
- Does the role involve coaching world-class scientists? (-2)

## The Company
- Is the company a top-tier one (e.g., Google, Apple, Meta, Helsing, Mistral AI, Perplexity, OpenAI, Anthropic, Nvidia)? (+2)
- Does the company have more than 150 employees? (-1)
- Does the company offer a full-remote option? (+2)
- Is this a consulting job for a standard consulting firm? (-1)
- Is the company in the defense sector? (+2)
- Is the company in the robotics sector? (+2)

^ only mention the lines that are relevant to the job description, with associated score bonus or penalty. 
For example, do not output "- Leading a team: No (+0)". Instead do not output anything for this criteria.
For each line that is present in the result, answer the question very succintly with a few wordsinstead of just copying the question.

---
## Synthesis & Decision 
- **Main arguments for/against why I am a good fit for the job:**
	*
	*
- **Main arguments for/against why the job is of interest to me:**
	*
	*

Answer only with a json object with the following structure:
	"evaluation_grid" # text of the evaluation grid and the synthesis pointsS
    "score" # score between 0 and 10
    "preferred_pitch" # 1: Large Group, 2: Startup, 3: General Tech, 4: General

















