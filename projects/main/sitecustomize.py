from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is on sys.path so imported sub-pipelines
# can resolve their own skills modules via package path like
# 'projects.<name>.skills.<module>'.
try:
    here = Path(__file__).resolve()
    repo_root = here.parents[2]  # repo_root/projects/main/sitecustomize.py
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
except Exception:
    pass

