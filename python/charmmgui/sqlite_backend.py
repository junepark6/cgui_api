"""
SQLite backend for CHARMM-GUI job history.

Used when STORAGE_BACKEND = "sqlite" in config.py.
"""

import json
import sqlite3
from datetime import datetime, timedelta

from .config import SQLITE_DB_FILE


# -----------------------------------------------------------
# Connection helper
# -----------------------------------------------------------
def _connect():
    return sqlite3.connect(SQLITE_DB_FILE)


# -----------------------------------------------------------
# Initialize database and ensure table exists
# -----------------------------------------------------------
def init_db():
    """Create the SQLite database and job table if missing."""
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            jobid TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            parameters TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------------------------------------
# Insert job record
# -----------------------------------------------------------
def save_sqlite_record(jobid, params, module="quick_bilayer"):
    """
    Save job submission details to SQLite database.

    params is a dictionary; stored as JSON.
    """
    init_db()  # Safe call; only creates table if missing

    conn = _connect()
    cur = conn.cursor()

    record = (
        jobid,
        module,
        datetime.now().isoformat(),
        json.dumps(params)
    )

    cur.execute("""
        INSERT OR REPLACE INTO jobs (jobid, module, submitted_at, parameters)
        VALUES (?, ?, ?, ?)
    """, record)

    conn.commit()
    conn.close()


# -----------------------------------------------------------
# Fetch one job
# -----------------------------------------------------------
def get_job(jobid):
    conn = _connect()
    cur = conn.cursor()

    cur.execute("SELECT jobid, module, submitted_at, parameters FROM jobs WHERE jobid = ?", (jobid,))
    row = cur.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "jobid": row[0],
        "module": row[1],
        "submitted_at": row[2],
        "parameters": json.loads(row[3])
    }


# -----------------------------------------------------------
# List all jobs
# -----------------------------------------------------------
def list_jobs():
    conn = _connect()
    cur = conn.cursor()

    cur.execute("SELECT jobid, module, submitted_at FROM jobs ORDER BY submitted_at DESC")
    rows = cur.fetchall()

    conn.close()

    jobs = []
    for r in rows:
        jobs.append({
            "jobid": r[0],
            "module": r[1],
            "submitted_at": r[2],
        })

    return jobs


# -----------------------------------------------------------
# Delete job
# -----------------------------------------------------------
def delete_job(jobid):
    conn = _connect()
    cur = conn.cursor()

    cur.execute("DELETE FROM jobs WHERE jobid = ?", (jobid,))
    conn.commit()
    conn.close()

    return True


# -----------------------------------------------------------
# Clean old jobs
# -----------------------------------------------------------
def clean_jobs(days=7):
    """
    Delete local job history older than the retention window.

    CHARMM-GUI job folders are normally available for about one week, so the
    default keeps local history aligned with remote availability.
    """
    init_db()

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    conn = _connect()
    cur = conn.cursor()

    cur.execute("SELECT jobid FROM jobs WHERE submitted_at < ?", (cutoff,))
    jobids = [row[0] for row in cur.fetchall()]

    cur.execute("DELETE FROM jobs WHERE submitted_at < ?", (cutoff,))
    deleted = cur.rowcount

    conn.commit()
    conn.close()

    return {
        "deleted": deleted,
        "cutoff": cutoff,
        "jobids": jobids,
    }


# -----------------------------------------------------------
# Search jobs
# -----------------------------------------------------------
def search_jobs(text=None, module=None, after=None, before=None):
    """
    Search job history with optional filters:
      - text: search inside parameters JSON
      - module: filter by module name
      - after/before: submission timestamp boundaries
    """
    conn = _connect()
    cur = conn.cursor()

    query = "SELECT jobid, module, submitted_at, parameters FROM jobs WHERE 1=1"
    params = []

    # Module filter
    if module:
        query += " AND module = ?"
        params.append(module)

    # Date filter: after
    if after:
        query += " AND submitted_at >= ?"
        params.append(after)

    # Date filter: before
    if before:
        query += " AND submitted_at <= ?"
        params.append(before + "T23:59:59")

    # Text search inside parameters
    if text:
        query += " AND parameters LIKE ?"
        params.append(f"%{text}%")

    query += " ORDER BY submitted_at DESC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()

    results = []
    for jobid, module, submitted, params_json in rows:
        results.append({
            "jobid": jobid,
            "module": module,
            "submitted_at": submitted,
            "parameters": json.loads(params_json)
        })

    return results
