# -*- coding: utf-8 -*-
from pathlib import Path

def repo_root_for(module_file: str) -> Path:
    """
    Resolves the repository root as parent of src/.
    Use like: REPO_ROOT = repo_root_for(__file__)
    """
    return Path(module_file).resolve().parents[1]
