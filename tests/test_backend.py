# tests/test_backend.py
import sys
import os

# Determine DIAG_FILE path relative to this test file's location (tests/)
# so it writes to the project root (recipes_be/pytest_diag.txt)
DIAG_FILE = os.path.join(os.path.dirname(__file__), "..", "pytest_diag.txt")

with open(DIAG_FILE, "a") as f:
    f.write(f"[tests/test_backend.py] TOP LEVEL: sys.path: {sys.path}\n")
    f.write(f"[tests/test_backend.py] TOP LEVEL: CWD: {os.getcwd()}\n")

def test_diagnostic_import():
    with open(DIAG_FILE, "a") as f:
        f.write(f"[test_diagnostic_import] Current Working Directory: {os.getcwd()}\n")
        f.write(f"[test_diagnostic_import] sys.path: {sys.path}\n")
    
        try:
            f.write("[test_diagnostic_import] Attempting to import app.backend...\n")
            from app import backend
            f.write("[test_diagnostic_import] Successfully imported 'app.backend'.\n")
            f.write(f"[test_diagnostic_import]   type(backend): {type(backend)}\n")
            f.write(f"[test_diagnostic_import]   backend.__name__: {backend.__name__}\n")
            f.write(f"[test_diagnostic_import]   backend.__package__: {backend.__package__}\n")
            f.write(f"[test_diagnostic_import]   backend.__file__: {getattr(backend, '__file__', 'N/A')}\n")
        
            if hasattr(backend, 'app'):
                f.write("[test_diagnostic_import]   'app' attribute found in backend module.\n")
            else:
                f.write("[test_diagnostic_import]   'app' attribute NOT found in backend module.\n")
            
        except ImportError as e:
            f.write(f"[test_diagnostic_import] ImportError during 'from app import backend': {e}\n")
            import traceback
            # Redirect traceback.print_exc() to the file
            original_stderr = sys.stderr
            sys.stderr = f # Temporarily redirect stderr
            traceback.print_exc()
            sys.stderr = original_stderr # Restore stderr
            f.write("\n") # Add a newline after traceback
        except Exception as e:
            f.write(f"[test_diagnostic_import] Other exception during 'from app import backend': {e}\n")
            import traceback
            original_stderr = sys.stderr
            sys.stderr = f # Temporarily redirect stderr
            traceback.print_exc()
            sys.stderr = original_stderr # Restore stderr
            f.write("\n") # Add a newline after traceback
        f.write("-"*80 + "\n") # Separator
    assert True # Keep the test passing to see output
