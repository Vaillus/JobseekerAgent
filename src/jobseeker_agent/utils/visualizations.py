import json
from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker

from jobseeker_agent.utils.paths import load_reviews


def plot_scores_distribution():
    """
    Loads the reviews and plots the distribution of scores as a bar plot.
    """
    reviews = load_reviews()
    if not reviews:
        print("No reviews found.")
        return

    scores = [r["score"] for r in reviews]

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
