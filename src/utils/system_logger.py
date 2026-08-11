"""
system_logger.py

Provides JSON-based system logging for application events.
Archives log files when they become too large.
"""

import json
import os
from datetime import datetime


DATABASE_DIR = "database"
LOG_FILE = os.path.join(DATABASE_DIR, "system_logs.json")

# Constants to prevent unbounded log growth:
MAX_LOG_ENTRIES = 2000
MAX_FILE_SIZE = 5_000_000


def _load_logs():
    """
    Loads log entries from storage.
    
    Returns:
        logs (list): A list of existing system logs, or empty list.
    """
    if not os.path.exists(LOG_FILE):
        return []

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_logs(logs):
    """
    Persists log entries to storage.

    Automatically creates a new log archive if the maximum 
    file size is exceeded.
    """
    os.makedirs(DATABASE_DIR, exist_ok=True)

    if len(logs) > MAX_LOG_ENTRIES:
        logs = logs[-MAX_LOG_ENTRIES:]

    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_FILE_SIZE:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive = os.path.join(DATABASE_DIR, f"system_logs_{timestamp}.json")
        os.rename(LOG_FILE, archive)
        logs = logs[-200:] # Retain 200 most recent logs.

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f)


def write_log(action, user=None, role=None, category="system", details=None):
    """
    Appends a system log entry to the list.
    
    Used throughout the system to track activity.

    Args:
        action (str): A description of the logged action.
        user (str, optional): The username associated with the log.
        role (str, optional): The users role at the time of the event.
        category (str, optional): The logs category label.
        details (dict, optional): Metadata about the event.
    """
    if details is None:
        details = {}

    logs = _load_logs()

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "role": role,
        "category": category,
        "action": action,
        "details": details,
    }

    logs.append(log_entry)

    _save_logs(logs)