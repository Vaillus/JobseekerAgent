import re
from typing import List, Dict

def reorder_experiences(tex_content: str, ranked_experiences: List[str]) -> str:
    """
    Reorders the experience entries in the resume's .tex file content.
    """
    section_pattern = re.compile(r"(\\section{Experience}.*?)(?=\\section{|\\end{resume})", re.DOTALL)
    section_match = section_pattern.search(tex_content)
    if not section_match:
        return tex_content

    experience_section_content = section_match.group(1)
    
    # Find all individual experience entries
    entry_pattern = re.compile(r"(?:\\textbf{|Personal Project –).*?(?=\\vspace{-2mm})", re.DOTALL)
    entries = entry_pattern.findall(experience_section_content)
    
    # Add the vspace back to each entry as it's used as a delimiter
    entries = [entry + "\\vspace{-2mm}\n" for entry in entries]

    entry_map = {}
    for block in entries:
        key = "Unknown"
        if "\\textbf{Thales DMS}" in block: key = "Thales DMS"
        elif "Job-Seeking Agentic Workflow" in block: key = "JobseekerAgent"
        elif "Camera Calibration for Autonomous Vehicle" in block: key = "CameraCalibration"
        elif "\\textbf{IBM France}" in block: key = "IBM France"
        entry_map[key] = block

    # Build the new section
    new_entries_str = ""
    for exp_name in ranked_experiences:
        if exp_name in entry_map:
            new_entries_str += entry_map[exp_name]

    # Replace old entries block with the new one
    # We need to find the content between \section{Experience} and the next \section
    content_inside_section = re.search(r"\\section{Experience}(.*?)(?=\\section{|\\end{resume})", tex_content, re.DOTALL)
    if content_inside_section:
        old_block = content_inside_section.group(1)
        # Reconstruct the section with title and new entries
        new_section = f"\\section{{Experience}}\n{new_entries_str}"
        return tex_content.replace(f"\\section{{Experience}}{old_block}", new_section)

    return tex_content # Fallback

def reorder_skills(tex_content: str, ranked_skills: Dict[str, List[str]]) -> str:
    """
    Reorders the skills within each category in the resume's .tex file content.
    """
    skill_ranking = ranked_skills
    for category, skills in skill_ranking.items():
        tex_category = category

        # This more flexible pattern should find the category regardless of minor spacing issues
        pattern = re.compile(f"(\\{{\\\\sl\\s*{tex_category}:}})(.*?)(?=\\\\|\\n)", re.IGNORECASE)
        
        def replacer(match):
            prefix = match.group(1)
            new_skills_str = "; ".join(skills)
            return f"{prefix} {new_skills_str}"

        tex_content, count = pattern.subn(replacer, tex_content, count=1)
        if count == 0:
            print(f"Warning: Could not find skill category '{tex_category}' in resume to reorder.")
            
    return tex_content
