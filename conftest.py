import sys
import os

DIAG_FILE = os.path.join(os.path.dirname(__file__), "pytest_diag.txt")

with open(DIAG_FILE, "a") as f:
    f.write(f"[conftest.py] Current Working Directory: {os.getcwd()}\n")
    f.write(f"[conftest.py] Initial sys.path: {sys.path}\n")

# This file is used by pytest to modify sys.path before test collection.
# It ensures that the 'app' package can be found by tests.

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

with open(DIAG_FILE, "a") as f:
    f.write(f"[conftest.py] Modified sys.path: {sys.path}\n")
    f.write("-"*80 + "\n") # Separator
