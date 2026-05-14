# pretty.py
import json
import os
import time
from datetime import datetime


def _print_json_block(value, indent=2):
    """Print nested JSON-like content with indentation."""
    prefix = " " * indent
    rendered = json.dumps(value, indent=2, ensure_ascii=False)
    for line in rendered.splitlines():
        print(f"{prefix}{line}")


def _print_mapping_section(title, mapping):
    """Pretty-print a dict section with aligned scalar values."""
    print("-" * 60)
    print(f"{title}:")
    print("-" * 60)

    if not mapping:
        print("(none)")
        return

    max_key_len = max(len(str(key)) for key in mapping.keys())

    for key, value in mapping.items():
        key_label = str(key).ljust(max_key_len)

        if isinstance(value, dict):
            print(f"{key_label} :")
            _print_json_block(value, indent=2)
        elif isinstance(value, list):
            if all(not isinstance(item, (dict, list, tuple)) for item in value):
                print(f"{key_label} : {value}")
            else:
                print(f"{key_label} :")
                _print_json_block(value, indent=2)
        else:
            print(f"{key_label} : {value}")


def pretty_status(status):
    """
    Pretty-print the job status dictionary returned by the server.
    Expected keys include:
      - jobid
      - status
      - last_modified
      - last_output
      - last_30_lines
      - rqinfo (optional)
      - rank (optional)
    """

    if isinstance(status, dict) and "error" in status and "detail" in status:
        print("\n" + "=" * 60)
        print("STATUS ERROR")
        print("=" * 60)
        print(f"Error:   {status.get('error')}")
        print(f"Detail:  {status.get('detail')}")
        print("=" * 60 + "\n")
        return

    jobid = status.get("jobid", "N/A")
    state = status.get("status", "unknown")
    last_mod = status.get("lastOutTime", None)
    output = status.get("lastOutFile", "")
    tail = status.get("lastOutLine", "")

    # Optional fields for pending jobs
    rqinfo = status.get("rqinfo")
    rank = status.get("rank")

    # Normalize timestamp if possible
    if last_mod:
        try:
            dt = datetime.fromisoformat(last_mod)
            last_mod = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass

    print("\n" + "=" * 60)
    print(f"JOB STATUS SUMMARY for JobID: {jobid}")
    print("=" * 60)

    print(f"Status:         {state}")
    print(f"Last Modified:  {last_mod}")
    print("-" * 60)

    # --------------------------------------------------------
    # Special display for 'submitted' jobs (pending in queue)
    # --------------------------------------------------------
    if state == "submitted":
        print("⏳ Job is pending in the Redis Queue")
        print("-" * 60)

        # Number of jobs ahead
        if isinstance(rank, int):
            print(f"Jobs ahead in queue: {rank}")
        else:
            print("Jobs ahead in queue: (not provided)")

        print()

        # rqinfo block
        if rqinfo:
            print("Redis Queue Info (rqinfo):")
            print(rqinfo.strip())
        else:
            print("Redis Queue Info: (not provided)")

        print("-" * 60)

    # --------------------------------------------------------
    # Print normal log info for running / completed / error
    # --------------------------------------------------------
    print("Last Output File:")
    print(output if output else "(none)")
    print("-" * 60)

    print("Last 30 Lines of Log Output:")
    if tail:
        print(tail.rstrip())
    else:
        print("(no log output available)")
    print("=" * 60 + "\n")


def _text_or_na(value):
    if value is None or value == "" or isinstance(value, bool):
        return "N/A"
    return str(value)


def _first_present(mapping, paths):
    for path in paths:
        value = mapping
        for key in path:
            if not isinstance(value, dict) or key not in value:
                value = None
                break
            value = value[key]
        if value is not None:
            return value
    return None


def _extract_status_jobs(response):
    if isinstance(response, list):
        return response

    if isinstance(response, dict):
        for key in ("jobs", "data", "results"):
            value = response.get(key)
            if isinstance(value, list):
                return value

        if "jobid" in response or "JobID" in response:
            return [response]

    return []


def _format_created_date(value):
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        timestamp = int(value)
        if len(str(timestamp)) >= 13:
            timestamp = timestamp // 1000

        previous_tz = os.environ.get("TZ")
        date_tz = os.environ.get("TZ", "America/New_York")

        try:
            os.environ["TZ"] = date_tz
            if hasattr(time, "tzset"):
                time.tzset()
            return datetime.fromtimestamp(timestamp).strftime("%B %-d, %Y, %-I:%M:%S %p %Z")
        except Exception:
            return str(value)
        finally:
            if previous_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous_tz
            if hasattr(time, "tzset"):
                time.tzset()

    return _text_or_na(value)


def pretty_status_table(response):
    if isinstance(response, dict) and "error" in response and "detail" in response:
        print("\n" + "=" * 60)
        print("STATUS ERROR")
        print("=" * 60)
        print(f"Error:   {response.get('error')}")
        print(f"Detail:  {response.get('detail')}")
        print("=" * 60 + "\n")
        return

    jobs = _extract_status_jobs(response)
    if not jobs:
        return

    print(f"{'JobID':<14} {'Project':<24} {'module':<24} {'status':<12} {'date created':<32}")
    print(f"{'--------------':<14} {'------------------------':<24} {'------------------------':<24} {'------------':<12} {'--------------------------------':<32}")

    for job in jobs:
        if not isinstance(job, dict):
            continue

        jobid = _text_or_na(_first_present(job, (
            ("jobid",), ("JobID",), ("id",), ("request", "jobid")
        )))
        project = _text_or_na(_first_present(job, (
            ("project",), ("Project",), ("request", "project"), ("parameters", "project")
        )))
        module = _text_or_na(_first_present(job, (
            ("module",), ("modules",), ("Module",), ("request", "module"),
            ("request", "modules"), ("parameters", "module")
        )))
        status = _text_or_na(_first_present(job, (
            ("status",), ("state",), ("job_status",), ("request", "status")
        )))
        created = _format_created_date(_first_present(job, (
            ("date_created",), ("created_at",), ("created",), ("submitted_at",),
            ("creation_date",), ("dateCreated",)
        )))

        print(f"{jobid:<14} {project:<24} {module:<24} {status:<12} {created:<32}")

# --------------------------------------------------------------
# Pretty-print job record from JSON or SQLite
# --------------------------------------------------------------
def pretty_job_info(job):
    """
    Pretty-print a job record dictionary. Expected structure:
      {
        "jobid": "...",
        "module": "quick_bilayer",
        "submitted_at": "2025-12-11T20:15:01",
        "parameters": { ... },
        "output": { ... }   # optional
      }
    """
    if not job:
        print("❌ Job not found.")
        return

    jobid = job.get("jobid", "N/A")
    module = job.get("module", "N/A")
    submitted = job.get("submitted_at", "N/A")
    params = job.get("parameters", {})
    output = job.get("output")

    # Format submission timestamp
    try:
        dt = datetime.fromisoformat(submitted)
        submitted_fmt = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        submitted_fmt = submitted

    print("\n" + "="*60)
    print(f"JOB RECORD DETAILS for JobID: {jobid}")
    print("="*60)

    print(f"Module:          {module}")
    print(f"Submitted At:    {submitted_fmt}")

    _print_mapping_section("Parameters", params)

    if output is not None:
        _print_mapping_section("Output", output)

    print("="*60 + "\n")

def pretty_search_results(results):
    if not results:
        print("\nNo matching jobs found.\n")
        return

    print("\nSEARCH RESULTS")
    print("=" * 60)
    for job in results:
        print(f"JobID:       {job['jobid']}")
        print(f"Module:      {job['module']}")
        print(f"Submitted:   {job['submitted_at']}")

        # Example: show upper/lower/margin if present
        params = job["parameters"]
        important = {k: params[k] for k in params if k in ("upper", "lower", "margin", "membtype")}
        if important:
            print("Key Params:  ", important)

        print("-" * 60)
    print("=" * 60)
