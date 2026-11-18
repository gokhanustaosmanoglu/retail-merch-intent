"""Lets pytest find merchdb.py when it is run from the repository root."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
