import os
import re

# Recommended display order for known model sizes
_ORDER = ['tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en',
          'medium', 'medium.en', 'large', 'large-v1', 'large-v2', 'large-v3']


def _hf_cache_dir():
    return os.path.join(os.path.expanduser('~'), '.cache', 'huggingface', 'hub')


def _resolve_snapshot(model_dir):
    """Return the path to the model snapshot folder (with the actual files)."""
    snapshots = os.path.join(model_dir, 'snapshots')
    if not os.path.isdir(snapshots):
        return None
    # Prefer a snapshot that actually contains a model file
    candidates = [os.path.join(snapshots, s) for s in os.listdir(snapshots)]
    candidates = [c for c in candidates if os.path.isdir(c)]
    for c in candidates:
        if os.path.exists(os.path.join(c, 'model.bin')):
            return c
    return candidates[0] if candidates else None


def list_installed_models():
    """
    Scan the HuggingFace cache for installed faster-whisper models.

    Returns a list of dicts: {'name': 'large-v3', 'path': '<abs path to snapshot>'}.
    """
    cache = _hf_cache_dir()
    found = {}
    if os.path.isdir(cache):
        for entry in os.listdir(cache):
            m = re.match(r'models--Systran--faster-whisper-(.+)$', entry)
            if not m:
                continue
            name = m.group(1)
            path = _resolve_snapshot(os.path.join(cache, entry))
            if path:
                found[name] = path

    def sort_key(name):
        return _ORDER.index(name) if name in _ORDER else len(_ORDER)

    return [{'name': n, 'path': found[n]} for n in sorted(found, key=sort_key)]
