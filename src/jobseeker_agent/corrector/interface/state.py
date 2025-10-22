import threading
from typing import Optional

# Global state variables
JOB_ID: int = 270
JOB_DESCRIPTION: str = ""
JOB_DETAILS: dict = {}

# Threading objects
EXTRACTION_THREAD: Optional[threading.Thread] = None
DATA_LOADING_THREAD: Optional[threading.Thread] = None

# Status dictionaries
EXTRACTION_STATUS: dict = {"status": "idle", "error": None}
DATA_LOADING_STATUS: dict = {"status": "idle", "error": None}
