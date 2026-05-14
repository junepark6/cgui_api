import argparse
from getpass import getpass

from .client import CharmmGUIClient
from .quick_bilayer import QuickBilayer
from .config import PRETTY_STATUS_OUTPUT
from .config import ensure_paths
ensure_paths()

def main():
    parser = argparse.ArgumentParser(description="CHARMM-GUI API CLI")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logs")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress normal output")
    parser.add_argument("--baseurl", default=None, help="Override API base URL")

    sub = parser.add_subparsers(dest="cmd")

    # Login
    p_login = sub.add_parser("login")
    p_login.add_argument("--email")
    p_login.add_argument("--password")

    # Status
    p_status = sub.add_parser("status")
    p_status.add_argument("jobid_arg", nargs="?", help="Optional job ID to check")
    p_status.add_argument("--jobid", dest="jobid_flag", help="Optional job ID to check")

    # Job management
    p_jobs = sub.add_parser("jobs", help="Manage job history")
    p_jobs.add_argument("action", choices=["list", "info", "delete", "search", "clean"])
    p_jobs.add_argument("--jobid", help="Job ID for info/delete")
    p_jobs.add_argument("--contains", help="Text to search in parameters")
    p_jobs.add_argument("--module", help="Filter by module")
    p_jobs.add_argument("--after", help="Submitted after YYYY-MM-DD")
    p_jobs.add_argument("--before", help="Submitted before YYYY-MM-DD")
    p_jobs.add_argument("--days", type=int, default=7, help="Retention window for clean (default: 7)")

    # Quick Bilayer
    p_qb = sub.add_parser("bilayer")
    p_qb.add_argument("--jobid")
    p_qb.add_argument("--membrane-only", action="store_true")
    p_qb.add_argument("--upper")
    p_qb.add_argument("--lower")
    p_qb.add_argument("--membtype")
    p_qb.add_argument("--margin", type=float, required=True)
    p_qb.add_argument("--wdist", type=float, default=22.5)
    p_qb.add_argument("--ion-conc", type=float, default=0.15)
    p_qb.add_argument("--ion-type", default="NaCl")

    for flag in ["clone_job", "run_ffconverter", "run_ppm",
                 "prot_projection_upper", "prot_projection_lower"]:
        p_qb.add_argument(f"--{flag}", action="store_true")

    # Download
    p_dl = sub.add_parser("download")
    p_dl.add_argument("--jobid", required=True)
    p_dl.add_argument("-o", "--out", default="charmm-gui.tgz")

    args = parser.parse_args()

    # Create shared client
    client = CharmmGUIClient(
        verbose=args.verbose,
        quiet=args.quiet,
        base_url=args.baseurl
    )

    # Dispatch
    if args.cmd == "login":
        email = args.email or input("Email: ")
        password = args.password or getpass("Password: ")
        client.email = email
        client.password = password
        client.login()
        client.save_token()
        return

    elif args.cmd == "status":
        jobid = args.jobid_flag or args.jobid_arg
        if args.jobid_flag and args.jobid_arg and args.jobid_flag != args.jobid_arg:
            parser.error("status accepts only one jobid")

        client.token = CharmmGUIClient.load_token()
        st = client.status(jobid)

        if PRETTY_STATUS_OUTPUT:
            from .pretty import pretty_status, pretty_status_table
            if jobid:
                pretty_status(st)
            else:
                pretty_status_table(st)
        else:
            import json
            print(json.dumps(st, indent=2))

        return

    elif args.cmd == "bilayer":
        client.token = CharmmGUIClient.load_token()
        qb = QuickBilayer(client)
        params = vars(args)
        del params["cmd"]
        qb.submit(**params)
        return

    elif args.cmd == "download":
        client.token = CharmmGUIClient.load_token()
        client.download(args.jobid, outfile=args.out)
        return

    elif args.cmd == "jobs":
        from .sqlite_backend import list_jobs, get_job, delete_job
        from .config import STORAGE_BACKEND
        from .pretty import pretty_job_info

        if STORAGE_BACKEND != "sqlite":
            print("⚠ SQLite backend not enabled. Set STORAGE_BACKEND = 'sqlite' in config.py.")
            return

        # List jobs
        if args.action == "list":
            items = list_jobs()
            if not items:
                print("No jobs found in SQLite history.")
                return

            print("\nSaved Jobs:")
            print("=" * 60)
            for item in items:
                print(f"{item['jobid']:>12}  |  {item['module']:<15}  |  {item['submitted_at']}")
            print("=" * 60)
            return

        # Job info
        elif args.action == "info":
            if not args.jobid:
                print("Specify --jobid")
                return

            job = get_job(args.jobid)
            if PRETTY_STATUS_OUTPUT:
                pretty_job_info(job)
            else:
                print(job)
            return

        # Delete job
        elif args.action == "delete":
            if not args.jobid:
                print("Specify --jobid")
                return

            delete_job(args.jobid)
            print(f"Deleted job {args.jobid}")
            return

        # Clean old jobs
        elif args.action == "clean":
            clean_job_history(args.days)
            return

        # Search jobs
        elif args.action == "search":
            from .sqlite_backend import search_jobs
            from .pretty import pretty_search_results
        
            results = search_jobs(
                text=args.contains,
                module=args.module,
                after=args.after,
                before=args.before,
            )
        
            if PRETTY_STATUS_OUTPUT:
                pretty_search_results(results)
            else:
                print(results)
            return

    parser.print_help()


def clean_job_history(days):
    from .sqlite_backend import clean_jobs
    from .config import STORAGE_BACKEND

    if STORAGE_BACKEND != "sqlite":
        print("⚠ SQLite backend not enabled. Set STORAGE_BACKEND = 'sqlite' in config.py.")
        return

    if days < 0:
        print("--days must be 0 or greater")
        return

    result = clean_jobs(days=days)
    print(
        f"Deleted {result['deleted']} job(s) submitted before "
        f"{result['cutoff']} (retention: {days} days)."
    )


if __name__ == "__main__":
    main()
