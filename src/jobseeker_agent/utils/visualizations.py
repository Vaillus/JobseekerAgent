import json
from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

from jobseeker_agent.utils.paths import load_main_evals


def plot_scores_distribution():
    """
    Loads the main evaluations and plots the distribution of scores as a bar plot.
    """
    evals = load_main_evals()
    if not evals:
        print("No evaluations found.")
        return

    scores = [e["score"] for e in evals]

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    sns.histplot(data=scores, bins=10, kde=False, color="skyblue")
    
    ax = plt.gca()
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.title("Distribution of Job Offer Scores", fontsize=16, fontweight='bold')
    plt.xlabel("Score", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


if __name__ == "__main__":
    plot_scores_distribution()
