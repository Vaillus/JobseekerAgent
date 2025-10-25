import threading
from typing import Optional

# Global state variables
JOB_ID: int = 270
JOB_DESCRIPTION: str = ""
JOB_DETAILS: dict = {}

# Threading objects
EXTRACTION_THREAD: Optional[threading.Thread] = None
DATA_LOADING_THREAD: Optional[threading.Thread] = None
RANKING_THREAD: Optional[threading.Thread] = None
INTRODUCTION_THREAD: Optional[threading.Thread] = None
SCRAPING_THREAD: Optional[threading.Thread] = None
REVIEW_THREAD: Optional[threading.Thread] = None

# Status dictionaries
EXTRACTION_STATUS: dict = {"status": "idle", "error": None}
DATA_LOADING_STATUS: dict = {"status": "idle", "error": None}
RANKING_STATUS: dict = {"status": "idle", "error": None}
INTRODUCTION_STATUS: dict = {"status": "idle", "error": None}
SCRAPING_STATUS: dict = {"status": "idle", "new_jobs_count": 0, "error": None}
REVIEW_STATUS: dict = {"status": "idle", "current": 0, "total": 0, "error": None}

