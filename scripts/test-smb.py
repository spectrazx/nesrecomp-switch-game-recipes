#!/usr/bin/env python3
"""Compatibility entry point for the Mario-owned regression suite."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[1] / 'games/smb1/tests/verify.py'), run_name='__main__')
