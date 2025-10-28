from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from pathlib import Path

from jobseeker_agent.utils.llm import get_llm

load_dotenv()


def load_local_prompt(prompt_name: str) -> str:
    """Load a prompt from the cover_letter directory."""
    prompt_path = Path(__file__).parent / f"{prompt_name}.md"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def write_cover_letter(
    job_description: str, 
    profil_pro: str, 
    synthesis_and_decision: str, 
    resume: str, 
    cover_letter_template: str, 
    model: str = "gemini-2.5-flash", 
    status_callback=None
) -> str:
    """
    Generate a cover letter through a multi-stage conversational workflow:
    1. Draft - Generate initial version
    2. Critique - Analyze and provide suggestions
    3. Correct - Apply corrections based on critique
    4. Compress - Reduce length if needed while maintaining quality
    """
    print("[COVER LETTER] Starting multi-stage generation workflow...")
    llm = get_llm(model)
    
    # Load system prompt and format with context
    system_prompt = load_local_prompt("system")
    system_message = SystemMessage(content=system_prompt.format(
        job_description=job_description,
        profil_pro=profil_pro,
        synthesis_and_decision=synthesis_and_decision,
        resume=resume
    ))
    
    # Initialize conversation with system message
    messages = [system_message]
    
    # Stage 1: Generate draft
    print("    [STAGE 1] Generating draft...")
    if status_callback:
        status_callback("Stage 1/4: Generating draft...")
    
    draft_prompt = load_local_prompt("draft")
    messages.append(HumanMessage(content=draft_prompt.format(
        cover_letter_template=cover_letter_template
    )))
    first_draft = llm.invoke(messages)
    messages.append(first_draft)
    wordcount = len(first_draft.content.split())
    print(f"    [STAGE 1] Draft generated ({wordcount} words)")
    if status_callback:
        status_callback(f"Stage 1/4: Draft generated ({wordcount} words)")
    
    # Stage 2: Critique the draft
    print("    [STAGE 2] Critiquing draft...")
    if status_callback:
        status_callback(f"Stage 2/4: Critiquing draft ({wordcount} words)")
    
    critic_prompt = load_local_prompt("critic")
    messages.append(HumanMessage(content=critic_prompt))
    critique = llm.invoke(messages)
    messages.append(critique)
    print(f"    [STAGE 2] Critique generated")
    
    # Stage 3: Correct based on critique
    print("    [STAGE 3] Correcting draft...")
    if status_callback:
        status_callback(f"Stage 3/4: Correcting based on critique ({wordcount} words)")
    
    corrector_prompt = load_local_prompt("corrector")
    messages.append(HumanMessage(content=corrector_prompt.format(
        wordcount=wordcount
    )))
    corrected = llm.invoke(messages)
    messages.append(corrected)
    wordcount = len(corrected.content.split())
    print(f"    [STAGE 3] Corrected draft generated ({wordcount} words)")
    if status_callback:
        status_callback(f"Stage 3/4: Corrected draft generated ({wordcount} words)")
    
    # Stage 4: Compress if needed
    if not (200 <= wordcount <= 300):
        print(f"    [STAGE 4] Compressing cover letter ({wordcount} words -> 200-300)...")
        if status_callback:
            status_callback(f"Stage 4/4: Compressing cover letter ({wordcount} words -> 200-300)")
        
        if wordcount > 300:
            wordcount_sentence = f"The letter should be between 200 and 300 words long. It is currently {wordcount} words long. It should be approximately {int((wordcount - 250)/wordcount*100)}% shorter."
        else:
            wordcount_sentence = f"The letter should be between 200 and 300 words long. It is currently {wordcount} words long. It should be approximately {int((250 - wordcount)/wordcount*100)}% longer."
        
        compressor_prompt = load_local_prompt("compressor")
        messages.append(HumanMessage(content=compressor_prompt.format(
            wordcount_sentence=wordcount_sentence
        )))
        compressed = llm.invoke(messages)
        messages.append(compressed)
        final_wordcount = len(compressed.content.split())
        print(f"    [STAGE 4] Compressed cover letter generated ({final_wordcount} words)")
        if status_callback:
            status_callback(f"Complete! Final cover letter: {final_wordcount} words")
        
        print("[COVER LETTER] Multi-stage workflow complete!")
        return compressed.content
    
    print("[COVER LETTER] Multi-stage workflow complete!")
    if status_callback:
        status_callback(f"Complete! Final cover letter: {wordcount} words")
    return corrected.content
