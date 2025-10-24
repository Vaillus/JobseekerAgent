import sys
from pathlib import Path
import webbrowser
import tempfile
import os

from rich.console import Console
from rich.table import Table

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from jobseeker_agent.utils.paths import load_test_reviews, load_labels, load_raw_jobs
from jobseeker_agent.scraper.extract_job_details import extract_job_details


def load_and_merge_data(generation_id: int):
    """Loads reviews, labels, and raw job data and merges them."""
    reviews = load_test_reviews(generation_id)
    labels = load_labels(generation_id)
    raw_jobs = load_raw_jobs()
    print(f"Loaded {len(reviews)} reviews, {len(labels)} labels, and {len(raw_jobs)} raw jobs.")
    if not labels:
        print(f"Warning: No labels found for generation {generation_id}.")
        return []

    reviews_map = {e["id"]: e for e in reviews}
    raw_jobs_map = {j["id"]: j for j in raw_jobs}

    merged_data = []
    for label in labels:
        job_id = label["id"]
        if job_id in reviews_map and job_id in raw_jobs_map:
            # Ensure score is a number, default to 0 if not present or invalid
            score = reviews_map[job_id].get("score", 0)
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = 0

            merged_item = {
                **label,
                **reviews_map[job_id],
                **raw_jobs_map[job_id],
                "score": score,
            }
            merged_data.append(merged_item)
    return merged_data


def find_optimal_threshold(data):
    """Finds the optimal score threshold to minimize classification error."""
    if not data:
        return None, 0

    scores = [d["score"] for d in data]
    labels = [d["interested"] for d in data]

    unique_scores = sorted(list(set(scores)))

    if not unique_scores:
        return None, len([l for l in labels if l])

    # Generate potential thresholds between unique scores
    thresholds = [unique_scores[0] - 0.1]
    for i in range(len(unique_scores) - 1):
        thresholds.append((unique_scores[i] + unique_scores[i + 1]) / 2)
    thresholds.append(unique_scores[-1] + 0.1)

    best_threshold = None
    min_errors = float("inf")

    for threshold in thresholds:
        errors = 0
        for score, label in zip(scores, labels):
            prediction = score >= threshold
            if prediction != label:
                errors += 1

        if errors < min_errors:
            min_errors = errors
            best_threshold = threshold

    return best_threshold, min_errors


def display_misclassified_job(job, prediction):
    """Creates a temporary HTML file with job details and opens it in the browser."""
    print(f"Fetching details for job ID {job['id']}...")
    job_details = extract_job_details(job["job_link"])
    if not job_details:
        print(f"Could not retrieve details for job ID {job['id']}.")
        return

    html_content = f"""
    <html>
    <head>
        <title>Misclassified Job: {job['title']}</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; padding: 2em; max-width: 1200px; margin: auto; display: flex; gap: 2em; }}
            .column {{ flex: 1; overflow: auto; }}
            .description {{ border-right: 1px solid #ccc; padding-right: 2em;}}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; border-bottom: 1px solid #ccc; padding-bottom: 5px;}}
            pre {{ white-space: pre-wrap; color: #34495e; font-family: monospace; background-color: #f8f8f8; padding: 1em; border: 1px solid #ddd; border-radius: 5px;}}
            .info {{ background-color: #f8d7da; border-left: 5px solid #e74c3c; padding: 1em; margin-bottom: 2em; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="column description">
            <h1>{job['title']}</h1>
            <h2>{job['company']} - {job['location']}</h2>
            <hr>
            <h3>Full Job Description</h3>
            <pre>{job_details.get('description', 'Not available.')}</pre>
        </div>
        <div class="column evaluation">
            <div class="info">
                <h3>Classification Mismatch</h3>
                <p><b>ID:</b> {job['id']}</p>
                <p><b>Score:</b> {job['score']}</p>
                <p><b>Prediction (Threshold &gt;= {job['threshold']:.2f}):</b> {'Interested' if prediction else 'Not Interested'}</p>
                <p><b>Actual Label:</b> {'Interested' if job['interested'] else 'Not Interested'}</p>
            </div>
            <h2>Evaluation Grid</h2>
            <pre>{job.get('evaluation_grid', 'Not available.')}</pre>
        </div>
    </body>
    </html>
    """

    with tempfile.NamedTemporaryFile(
        "w", delete=False, suffix=".html", encoding="utf-8"
    ) as f:
        f.write(html_content)
        webbrowser.open("file://" + os.path.realpath(f.name))


def get_misclassified_jobs(data, threshold):
    """Identifies and sorts misclassified jobs."""
    misclassified_jobs = []
    for item in data:
        prediction = item["score"] >= threshold
        if prediction != item["interested"]:
            item_with_threshold = {**item, "threshold": threshold}
            misclassified_jobs.append((item_with_threshold, prediction))

    # Sort by the absolute difference between the score and the threshold
    misclassified_jobs.sort(key=lambda x: abs(x[0]["score"] - threshold), reverse=True)
    return misclassified_jobs


def visualize_misclassified_jobs(misclassified_jobs):
    """Displays misclassified jobs one by one in a browser."""
    if not misclassified_jobs:
        print("No misclassified jobs to visualize.")
        return

    print(
        f"\nDisplaying {len(misclassified_jobs)} misclassified jobs one by one..."
    )

    for job, prediction in misclassified_jobs:
        display_misclassified_job(job, prediction)
        try:
            input(
                "Press Enter to see the next misclassified job, or Ctrl+C to exit..."
            )
        except KeyboardInterrupt:
            print("\nExiting visualization.")
            break


def find_confident_correct_jobs(data, threshold):
    """
    Finds correctly categorized jobs with a score more than 2.5 away from the threshold.
    """
    confident_job_ids = []
    for item in data:
        prediction = item["score"] >= threshold
        is_correct = prediction == item["interested"]
        is_confident = abs(item["score"] - threshold) > 2.5

        if is_correct and is_confident:
            confident_job_ids.append(item["id"])

    return confident_job_ids


def main(generation_id: int):
    """Main function to analyze job reviews."""
    console = Console()

    console.print(f"[bold cyan]Analysis for Generation ID: {generation_id}[/bold cyan]")

    console.print("[bold cyan]1. Loading and merging data...[/bold cyan]")
    data = load_and_merge_data(generation_id)
    if not data:
        console.print("[bold red]No labeled reviews found for this generation. Exiting.[/bold red]")
        return
    console.print(f"-> Loaded {len(data)} labeled reviews.")

    # Display label distribution
    interested_count = sum(1 for d in data if d["interested"])
    not_interested_count = len(data) - interested_count

    labels_table = Table(title="Label Distribution")
    labels_table.add_column("Category", style="magenta")
    labels_table.add_column("Count", style="green")
    labels_table.add_row("Interested (Accepted)", str(interested_count))
    labels_table.add_row("Not Interested (Refused)", str(not_interested_count))
    console.print(labels_table)

    console.print("\n[bold cyan]2. Finding optimal score threshold...[/bold cyan]")
    threshold, min_errors = find_optimal_threshold(data)

    if threshold is None:
        console.print("[bold red]Could not determine an optimal threshold.[/bold red]")
        return

    accuracy = 1 - (min_errors / len(data))

    table = Table(title="Optimal Threshold Results")
    table.add_column("Metric", style="magenta")
    table.add_column("Value", style="green")
    table.add_row("Optimal Threshold", f"{threshold:.2f}")
    table.add_row("Minimum Errors", f"{min_errors} / {len(data)}")
    table.add_row("Accuracy", f"{accuracy:.2%}")
    console.print(table)

    console.print("\n[bold cyan]3. Finding confidently correct jobs...[/bold cyan]")
    confident_ids = find_confident_correct_jobs(data, threshold)
    if confident_ids:
        console.print(
            f"-> Found {len(confident_ids)} correctly classified jobs with a score margin > 2.5 from the threshold."
        )
        console.print(f"IDs: {confident_ids}")
    else:
        console.print("-> No confidently correct jobs found with a margin > 2.5.")

    console.print("\n[bold cyan]4. Identifying misclassified jobs...[/bold cyan]")
    misclassified_jobs = get_misclassified_jobs(data, threshold)

    if not misclassified_jobs:
        console.print(
            "[bold green]No misclassified jobs found. Congratulations![/bold green]"
        )
    else:
        misclassified_ids = [job[0]["id"] for job in misclassified_jobs]
        console.print(f"-> Found {len(misclassified_jobs)} misclassified jobs.")
        console.print(f"IDs (sorted by error magnitude): {misclassified_ids}")

        console.print("\n[bold cyan]5. Visualizing misclassified jobs...[/bold cyan]")
        visualize_misclassified_jobs(misclassified_jobs)

    console.print("\n[bold green]Analysis complete.[/bold green]")


if __name__ == "__main__":
    generation_id = 4
    main(generation_id)
    # check_scores(generation_id)
