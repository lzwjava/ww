"""conftest.py — collect tests that mock sys.modules last to avoid polluting others."""

# Modules that inject sys.modules at import time should run last
_DEFERRED_PREFIXES = [
    "tests/audio/test_audio_pipeline",
]


def pytest_collection_modifyitems(items):
    """Sort so that deferred tests run last."""
    normal = []
    deferred = []
    for item in items:
        path = str(item.fspath)
        if any(path.endswith(p) or p in path for p in _DEFERRED_PREFIXES):
            deferred.append(item)
        else:
            normal.append(item)
    items[:] = normal + deferred
