# Input data
## Job description
{job_description}
## Candidate profile
{profil_pro}
## Synthesis and decision
{synthesis_and_decision}
## Candidate resume
{resume}
## Cover letter template
{cover_letter_template}


# Task
Write a cover letter for the job by modifying the LaTeX template provided.
You MUST return the COMPLETE LaTeX file with all its structure (\documentclass, \usepackage, \begin{{document}}, etc.).

Instructions:
1. Replace the \companyname and \jobtitle commands with the actual company name and job title from the job description.
2. Keep the entire LaTeX document structure intact (preamble, document environment, letter environment, etc.).
3. Modify ONLY the content between the comments:
   - For the first part (between "% first part starts here" and "% first part ends here"): Identify the company's mission and how it corresponds to the candidate's profile.
   - For the second part (between "% second part starts here" and "% second part ends here"): Highlight 2 or 3 **experiences or key skills** (hard and soft skills) that correspond to the requirements of the offer. **Illustrate** always with concrete examples or quantified results. Mention them in the same order as in the resume.
   - For the third part (between "% third part starts here" and "% third part ends here"): Write a wrap-up that summarizes what has been said by putting a term on my profile (e.g., "versatile problem solver"), and that reminds that I am fully aligned with their mission.
4. Keep everything else from the template unchanged (opening, closing, signature block, etc.).

Return the complete LaTeX file as a valid .tex document that can be compiled directly.