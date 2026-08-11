"""
settings_store.py

Provides persistent application settings storage using a JSON file.
A default set of settings is outline if the file is missing.
"""
import json
import os

SETTINGS_PATH = "database/user_settings.json"


DEFAULT_SETTINGS = {
    "theme": "light",
    "compute_mode": "auto",
    "confirm_on_enrol": False,
    "batch_size": 10
}

_settings_cache = None


def load_settings():
    """
    Load user-specific settings from disk or use defaults.
    """
    global _settings_cache

    if _settings_cache is not None:
        return _settings_cache

    if not os.path.exists(SETTINGS_PATH):
        _settings_cache = DEFAULT_SETTINGS.copy()
        save_settings(_settings_cache)
        return _settings_cache

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = DEFAULT_SETTINGS.copy()

    for key, value in DEFAULT_SETTINGS.items():
        data.setdefault(key, value)

    _settings_cache = data
    return _settings_cache


def save_settings(settings: dict):
    """
    Save settings to disk and update the cache.
    """
    global _settings_cache
    _settings_cache = settings

    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)