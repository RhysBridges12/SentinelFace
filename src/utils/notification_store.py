"""
notification_store.py

Provides persistent notification storage for both profile and
user-specific notifications using JSON files.

Notifications disappear after a set time period.
"""

import os
import json
from datetime import datetime, timedelta


DATABASE_DIR = "database"
SYSTEM_LOG = os.path.join(DATABASE_DIR, "system_notifications.json")
USER_NOTIF_DIR = os.path.join(DATABASE_DIR, "user_notifications")

# Time in hours until notifications expire:
EXPIRY_HOURS = 24


def _load_file(path):
    """
    Load JSON data from disk.

    Returns:
        list: Stored notification entries, or an empty list.
    """
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_file(path, data):
    """
    Persists notification data to disk.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _user_path(username):
    """
    Constructs the notification file path for a specific user.
    """
    return os.path.join(USER_NOTIF_DIR, f"{username}.json")


def load_notifications(path=SYSTEM_LOG, username=None):
    """
    Loads active notifications from storage.

    Expired notifications are automatically removed during loading.

    Args:
        path (str, optional): The file path for notifications.
        username (str, optional): Username for user-specific storage.

    Returns:
        list: Notification entries.
    """
    if username:
        path = _user_path(username)

    data = _load_file(path)

    now = datetime.now()
    notifications = []

    for item in data:
        try:
            ts = datetime.fromisoformat(item["timestamp"])
        except Exception:
            continue

        if now - ts < timedelta(hours=EXPIRY_HOURS):
            notifications.append(item)

    _save_file(path, notifications)

    return notifications


def save_notification(message, severity="info", username=None, path=SYSTEM_LOG):
    """
    Stores a new notification entry.

    Args:
        message (str): The notifications content.
        severity (str, optional): The notifications severity level.
        username (str, optional): The user that the note is for.
        path (str, optional): The storage path for system notifications.
    """
    if username:
        path = _user_path(username)

    data = _load_file(path)

    data.append({
        "message": message,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
    })

    _save_file(path, data)