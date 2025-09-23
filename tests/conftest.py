# Ensure project root is in sys.path for all tests
import sys, os

# Add the project root (one level above tests/) to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
