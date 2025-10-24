# Corrector - Resume Optimization and Personalization Module

This directory contains all the modules related to optimizing and personalizing resume content for specific job opportunities using AI agents.

## Agents

The `agents/` subdirectory contains the core AI agents responsible for different aspects of resume optimization.

### **`agents/keyword_extractor.py`**

Extracts and categorizes keywords from a job description against the candidate's profile. Returns keywords grouped by domain and classified into three categories: present in resume (match_present), mentioned in profile but absent in resume (match_absent), and remaining keywords (mismatch_absent). Also provides three resume title suggestions tailored to the job.

### **`agents/keyword_executor.py`**

Executes specific keyword modification instructions on the resume. Takes explicit edit instructions and applies them to produce a modified resume with proper LaTeX formatting.

### **`agents/ranker.py`**

Ranks experiences and skills by relevance to a specific job. Returns structured rankings for work experiences and skill categories (expertise, programming languages, technologies). Includes helper functions `reorder_experiences()` and `reorder_skills()` to apply rankings to LaTeX resume files.

### **`agents/title_corrector.py`**

Corrects and optimizes the resume title to better match the job description and candidate profile.

### **`agents/introducer.py`**

Suggests opening lines (introduction/summary) for the resume that highlight the most relevant aspects of the candidate's background for the specific job.
