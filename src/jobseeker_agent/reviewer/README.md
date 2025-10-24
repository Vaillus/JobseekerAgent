# Reviewer - Job Review and Evaluation Module

This directory contains all the modules related to reviewing, labeling, and analyzing job listings using AI agents and manual evaluation.

## Core Script

### **`review_batch.py`**

The main executable script for batch reviewing jobs. It defines a `JobReviewer` class that identifies unprocessed jobs, runs the AI reviewer agent, and saves the results. This is used for production job reviews that are stored in the main reviews database.

## Agents

### **`agents/reviewer.py`**

Contains the `review()` function, which is the core AI agent responsible for evaluating individual jobs. It uses an LLM to generate structured evaluations including an evaluation grid with multiple criteria, an overall score, and synthesis with decision recommendations.

## Evaluation Workflow

The `evaluation/` subdirectory contains scripts for testing and validating different versions (or "generations") of the reviewer agent.

### **`evaluation/label_jobs.py`**

An interactive command-line tool for manually labeling jobs as "interested" or "not interested." It displays each job in a browser for manual review and prompts you to provide a label. These labels form the ground truth dataset used for evaluating the AI reviewer's performance.

### **`evaluation/evaluate_reviewer.py`**

Runs evaluation experiments on a specific "generation" of the reviewer model. It takes manually labeled jobs, runs the AI reviewer on them using a specified LLM model or prompt variant, and saves the results in a separate test directory for analysis.

### **`evaluation/print_evaluation_result.py`**

Analyzes the performance of a reviewer generation against the manually labeled ground truth. It calculates accuracy, finds the optimal classification threshold to maximize correctness, identifies and visualizes misclassified jobs, and provides detailed performance metrics.

## Debuging

The `debugging/` subdirectory contains helper scripts for debugging and data integrity checks.

### **`debugging/view_single_review.py`**

A utility script to view the detailed review of a single, already-reviewed job by providing its ID. It fetches the job information and review data, then displays everything in the browser for inspection.

### **`debugging/check_scores.py`**

A validation utility that verifies the integrity of review data. It checks that each job's overall score matches the sum of the individual criterion scores from its evaluation grid, helping catch data inconsistencies.

