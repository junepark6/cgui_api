"""
CHARMM-GUI Python Client Configuration

Users can modify these settings to control:
 - Job history storage (JSON, SQLite, or disabled)
 - Job record directory or database file path
 - Token file location
 - Default verbosity behavior
"""

import os


# -----------------------------
#  STORAGE BACKEND
# -----------------------------
# "json"   → save job records as JSON files (recommended, default)
# "sqlite" → save job records in SQLite database (optional)
# "none"   → do not save job records

STORAGE_BACKEND = "sqlite"       # default recommended option


# -----------------------------
#  PATHS
# -----------------------------
# Where token is stored
TOKEN_FILE = os.path.expanduser("~/.charmmgui_token")

# Where job records should be saved (Option 1: JSON directory)
JOB_RECORD_DIR = os.path.expanduser("~/.charmmgui/jobs")

# SQLite DB file (Option 2: SQLite backend)
SQLITE_DB_FILE = os.path.expanduser("~/.charmmgui/job_history.db")


# ---------------------------------------------------------
# Pretty output settings
# ---------------------------------------------------------
# If True → use pretty print for job status
# If False → print raw JSON for job status
PRETTY_STATUS_OUTPUT = True


# -----------------------------
#  VERBOSE / QUIET Defaults
# -----------------------------
# CLI can override these, but they are the defaults
VERBOSE_DEFAULT = False
QUIET_DEFAULT = False


# -----------------------------
#  AUTO-CREATE DIRECTORIES
# -----------------------------
def ensure_paths():
    """Create directories as needed based on current storage backend."""
    if STORAGE_BACKEND == "json":
        os.makedirs(JOB_RECORD_DIR, exist_ok=True)

    if STORAGE_BACKEND == "sqlite":
        os.makedirs(os.path.dirname(SQLITE_DB_FILE), exist_ok=True)

    # Token file directory
    tokendir = os.path.dirname(TOKEN_FILE)
    if tokendir and not os.path.exists(tokendir):
        os.makedirs(tokendir, exist_ok=True)
