"""
Lightweight helpers for loading config.json and channels.json.
"""

import json
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))


def _load_json(filename: str) -> dict:
    path = os.path.join(_ROOT, filename)
    with open(path, 'r') as f:
        return json.load(f)


def get_folder_id(name: str, fallback: str = None) -> str:
    """
    Return a Drive folder ID by logical name.

    Names are defined in config.json["folders"].
    Falls back to ``fallback`` (or raises KeyError) if not found.
    """
    try:
        folders = _load_json('config.json').get('folders', {})
        return folders.get(name) or fallback or _raise(KeyError(f"Folder '{name}' not in config.json"))
    except FileNotFoundError:
        if fallback:
            return fallback
        raise


def get_channels(batch_name: str) -> list:
    """
    Return the channel list for a batch from channels.json.

    Each entry is either a plain URL string or a dict with at least a 'url' key.
    """
    data = _load_json('channels.json')
    batch = data.get(batch_name)
    if batch is None:
        raise KeyError(f"Batch '{batch_name}' not found in channels.json. Available: {list(data.keys())}")
    return batch


def get_config() -> dict:
    """Return the full config.json dict."""
    return _load_json('config.json')


def _raise(exc):
    raise exc
