from dotenv import load_dotenv
from langchain.schema import HumanMessage
import re
from pathlib import Path

from jobseeker_agent.utils.llm import get_llm

load_dotenv()


def load_local_prompt(prompt_name: str) -> str:
    """Load a prompt from the cover_letter directory."""
    prompt_path = Path(__file__).parent / f"{prompt_name}.md"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def escape_latex_special_chars(text: str) -> str:
    """
    Escape LaTeX special characters in text while preserving LaTeX commands.
    Only escapes & characters that are not part of LaTeX commands.
    """
    # Find all text between the three comment blocks (first part, second part, third part)
    # These are the sections where the LLM writes free text that might have unescaped &
    
    # Pattern to match content between % first part starts here and % first part ends here
    first_part_pattern = r'(% first part starts here\n)(.*?)(% first part ends here)'
    second_part_pattern = r'(% second part starts here\n)(.*?)(% second part ends here)'
    third_part_pattern = r'(% third part starts here\n)(.*?)(% third part ends here)'
    
    def escape_ampersands(match):
        prefix = match.group(1)
        content = match.group(2)
        suffix = match.group(3)
        # Escape & that are not already escaped and not part of LaTeX commands
        content = re.sub(r'(?<!\\)&', r'\\&', content)
        return prefix + content + suffix
    
    text = re.sub(first_part_pattern, escape_ampersands, text, flags=re.DOTALL)
    text = re.sub(second_part_pattern, escape_ampersands, text, flags=re.DOTALL)
    text = re.sub(third_part_pattern, escape_ampersands, text, flags=re.DOTALL)
    
    return text


def write_draft(job_description: str, profil_pro: str, synthesis_and_decision: str, resume: str, cover_letter_template: str, model: str = "gpt-5", status_callback=None) -> str:
    """Generate the first draft of the cover letter."""
    print("    [STAGE 1] Generating draft...")
    if status_callback:
        status_callback("Stage 1/4: Generating draft...")
    cover_letter_prompt = load_local_prompt("cover_letter")
    llm = get_llm(model)
    
    # Escape curly braces in LaTeX content to avoid conflicts with .format()
    escaped_template = cover_letter_template.replace('{', '{{').replace('}', '}}')
    escaped_resume = resume.replace('{', '{{').replace('}', '}}')
    
    message = HumanMessage(content=cover_letter_prompt.format(
        job_description=job_description, 
        profil_pro=profil_pro, 
        synthesis_and_decision=synthesis_and_decision, 
        resume=escaped_resume, 
        cover_letter_template=escaped_template
    ))
    response = llm.invoke([message])
    print(f"    [STAGE 1] Draft generated ({len(response.content)} chars)")
    return response.content


def critique_draft(job_description: str, profil_pro: str, synthesis_and_decision: str, resume: str, first_draft: str, model: str = "gpt-5", status_callback=None) -> str:
    """Critique the first draft and provide suggestions."""
    print("    [STAGE 2] Critiquing draft...")
    if status_callback:
        status_callback("Stage 2/4: Critiquing draft...")
    critic_prompt = load_local_prompt("critic")
    llm = get_llm(model)
    
    # Escape curly braces in LaTeX content
    escaped_resume = resume.replace('{', '{{').replace('}', '}}')
    escaped_draft = first_draft.replace('{', '{{').replace('}', '}}')
    
    message = HumanMessage(content=critic_prompt.format(
        job_description=job_description,
        profil_pro=profil_pro,
        synthesis_and_decision=synthesis_and_decision,
        resume=escaped_resume,
        first_draft=escaped_draft
    ))
    response = llm.invoke([message])
    print(f"    [STAGE 2] Critique generated ({len(response.content)} chars)")
    return response.content


def correct_draft(job_description: str, profil_pro: str, synthesis_and_decision: str, resume: str, first_draft: str, critic: str, model: str = "gpt-5", status_callback=None) -> str:
    """Correct the draft based on the critique."""
    print("    [STAGE 3] Correcting draft...")
    if status_callback:
        status_callback("Stage 3/4: Correcting based on critique...")
    corrector_prompt = load_local_prompt("corrector")
    llm = get_llm(model)
    
    # Escape curly braces in LaTeX content
    escaped_resume = resume.replace('{', '{{').replace('}', '}}')
    escaped_draft = first_draft.replace('{', '{{').replace('}', '}}')
    escaped_critic = critic.replace('{', '{{').replace('}', '}}')
    
    message = HumanMessage(content=corrector_prompt.format(
        job_description=job_description,
        profil_pro=profil_pro,
        synthesis_and_decision=synthesis_and_decision,
        resume=escaped_resume,
        first_draft=escaped_draft,
        critic=escaped_critic
    ))
    response = llm.invoke([message])
    print(f"    [STAGE 3] Corrected draft generated ({len(response.content)} chars)")
    return response.content


def compress_draft(job_description: str, profil_pro: str, synthesis_and_decision: str, resume: str, cover_letter: str, model: str = "gpt-5", status_callback=None) -> str:
    """Compress the cover letter while maintaining LaTeX validity."""
    print("    [STAGE 4] Compressing cover letter...")
    if status_callback:
        status_callback("Stage 4/4: Compressing cover letter...")
    compressor_prompt = load_local_prompt("compressor")
    llm = get_llm(model)
    
    # Escape curly braces in LaTeX content
    escaped_resume = resume.replace('{', '{{').replace('}', '}}')
    escaped_cover_letter = cover_letter.replace('{', '{{').replace('}', '}}')
    
    message = HumanMessage(content=compressor_prompt.format(
        job_description=job_description,
        profil_pro=profil_pro,
        synthesis_and_decision=synthesis_and_decision,
        resume=escaped_resume,
        cover_letter=escaped_cover_letter
    ))
    response = llm.invoke([message])
    print(f"    [STAGE 4] Compressed cover letter generated ({len(response.content)} chars)")
    return response.content


def write_cover_letter(job_description: str, profil_pro: str, synthesis_and_decision: str, resume: str, cover_letter_template: str, model: str = "gpt-5", status_callback=None) -> str:
    """
    Generate a cover letter through a multi-stage workflow:
    1. Draft - Generate initial version
    2. Critique - Analyze and provide suggestions
    3. Correct - Apply corrections based on critique
    4. Compress - Reduce length while maintaining quality
    5. Escape - Fix LaTeX special characters
    """
    print("    [COVER LETTER] Starting multi-stage generation workflow...")
    
    # Stage 1: Generate draft
    draft = write_draft(job_description, profil_pro, synthesis_and_decision, resume, cover_letter_template, model, status_callback)
    
    # Stage 2: Critique the draft
    critique = critique_draft(job_description, profil_pro, synthesis_and_decision, resume, draft, model, status_callback)
    
    # Stage 3: Correct based on critique
    corrected = correct_draft(job_description, profil_pro, synthesis_and_decision, resume, draft, critique, model, status_callback)
    
    # Stage 4: Compress the corrected version
    compressed = compress_draft(job_description, profil_pro, synthesis_and_decision, resume, corrected, model, status_callback)
    
    # Stage 5: Escape LaTeX special characters
    print("    [STAGE 5] Escaping LaTeX special characters...")
    if status_callback:
        status_callback("Finalizing: Escaping special characters and compiling...")
    final = escape_latex_special_chars(compressed)
    print(f"    [STAGE 5] Final cover letter ready ({len(final)} chars)")
    
    print("    [COVER LETTER] Multi-stage workflow complete!")
    return final