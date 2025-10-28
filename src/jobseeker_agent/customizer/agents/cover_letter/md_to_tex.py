import re
from pathlib import Path


def escape_latex_special_chars(text: str) -> str:
    """Échappe les caractères spéciaux LaTeX."""
    replacements = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text


def extract_company_and_job(markdown_content: str) -> tuple[str, str]:
    """Extrait le nom de l'entreprise et le titre du poste du markdown."""
    lines = markdown_content.strip().split('\n')
    
    company = "Company Name"
    job_title = "Position"
    
    for line in lines[:10]:
        if 'Hiring Team' in line:
            match = re.search(r'Dear\s+([^\s]+)\s+Hiring\s+Team', line)
            if match:
                company = match.group(1)
        
        if 'position' in line.lower() or 'role' in line.lower():
            match = re.search(r'the\s+([^.]+?)\s+(?:position|role)', line, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
    
    return company, job_title


def markdown_to_latex_cover_letter(markdown_path: Path, output_path: Path) -> str:
    """Convertit un cover letter markdown en LaTeX."""
    
    # Charger le markdown
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Extraire company et job title
    company, job_title = extract_company_and_job(markdown_content)
    
    # Nettoyer le contenu
    lines = markdown_content.strip().split('\n')
    
    # Trouver le début (après "Dear...")
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('Dear'):
            content_start = i + 1
            break
    
    # Trouver la fin (avant "Thank you" OU "Best regards")
    content_end = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        line_lower = lines[i].lower()
        if 'thank you for your time' in line_lower or 'best regards' in line_lower or 'sincerely' in line_lower:
            if 'thank you' in line_lower:
                content_end = i + 1
                for j in range(i + 1, len(lines)):
                    if not lines[j].strip() or 'best regards' in lines[j].lower():
                        content_end = j
                        break
                break
            else:
                content_end = i
                break
    
    # Extraire le contenu
    content_lines = lines[content_start:content_end]
    content = '\n'.join(content_lines).strip()
    
    # Échapper caractères spéciaux
    content_escaped = escape_latex_special_chars(content)
    
    # Construire le LaTeX
    latex_content = f"""\\documentclass[10pt]{{letter}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{lmodern}}
\\usepackage[english]{{babel}}
\\newcommand{{\\companyname}}{{{company}}}
\\newcommand{{\\jobtitle}}{{{job_title}}}
\\signature{{Hugo Vaillaud}}
\\address{{6 boulevard André Maurois \\\\ Paris 16e, France \\\\ hugovaillaud@gmail.com \\\\+ 33 6 50 98 57 75}}
\\date{{Paris, \\today}}
\\begin{{document}}
\\begin{{letter}}{{}}
\\opening{{Dear \\companyname \, Hiring Team,}}

{content_escaped}

\\closing{{Best regards,}}

\\end{{letter}}

\\end{{document}}
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    print(f"✅ Cover letter LaTeX généré: {output_path}")
    return latex_content

