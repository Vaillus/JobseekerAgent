import subprocess
from jobseeker_agent.utils.paths import get_data_path
from . import state


def compile_tex():
    """Compiles the TeX file to a PDF."""
    job_dir = get_data_path() / "resume" / f"{state.JOB_ID}"
    print(f"Compiling resume.tex for job {state.JOB_ID}...")
    result = subprocess.run(
        ["pdflatex", "-output-directory", str(job_dir), str(job_dir / "resume.tex")],
        capture_output=True,
        text=True,
    )
    print("Compilation finished.")
    if result.returncode != 0:
        print("--- LaTeX Compilation Error ---")
        print(result.stdout)
        print(result.stderr)
        return False, result.stdout
    return True, ""
