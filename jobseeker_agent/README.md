# Job Seeker Agent

## Project Goal

This project aims to automate the search for a new job and the application to job offers deemed interesting using LLM agents.

## Learning Objective

This project is also a way to learn and experiment with the Langgraph framework.

## Pipeline

The project pipeline consists of the following modules:

1.  **Job Scrapper**: A module to extract job offers from LinkedIn, with the possibility of adding other sources in the future.
2.  **Job Evaluator**: An agent responsible for filtering offers to keep only those that match my profile and interests.
3.  **Document Customization**: Once the offers are selected, this module adapts the CV and cover letter using my personal information so that they correspond to both my profile and the employer's expectations.
4.  **Form Filler (Optional)**: An agent that could be developed to automatically fill out online application forms.
