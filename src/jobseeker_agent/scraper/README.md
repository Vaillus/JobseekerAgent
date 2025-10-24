# Scraper - LinkedIn Job Scraping Module

This directory contains all the modules related to scraping, parsing, and managing job listings from LinkedIn.

## Modules

### **`run_scraper.py`**

The main executable script to launch a full scraping session. It uses `LinkedInJobsScraper` to find jobs based on predefined queries and saves them.

### **`linkedin_scraper.py`**

Contains the core `LinkedInJobsScraper` class, which handles the logic for fetching job search pages from LinkedIn and extracting initial job data (title, company, location, link).

### **`linkedin_query.py`**

A helper module for constructing complex search queries. It reads keywords from JSON files (e.g., job titles, fields, blacklist) and formats them into a LinkedIn-compatible search string.

### **`job_manager.py`**

Manages the local database of raw jobs (a JSON file). It handles loading, saving, and adding new jobs while preventing duplicates. It enriches new job data using other modules like `extract_job_details.py` and `date_parser.py`.

### **`extract_job_details.py`**

Analyzes a single LinkedIn job page URL to extract detailed information, including the full job description, the job's status (Open/Closed), and the workplace type (Remote/Hybrid/On-site).

### **`update_job_statuses.py`**

A maintenance script that iterates through all saved jobs in the database and uses `extract_job_details.py` to check if their status has changed (e.g., if a job has been closed).

### **`date_parser.py`**

A utility module that converts relative date strings from LinkedIn (e.g., "1 day ago") into a standard `YYYY-MM-DD` format.
