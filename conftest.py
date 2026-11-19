import sys
from pathlib import Path

# Make the package importable when running pytest from the repo root
# without installing the project first.
sys.path.insert(0, str(Path(__file__).resolve().parent))
