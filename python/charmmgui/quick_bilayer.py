import json, os, datetime
from .client import CharmmGUIClient
from .config import STORAGE_BACKEND, JOB_RECORD_DIR
from .sqlite_backend import save_sqlite_record

class QuickBilayer:
    def __init__(self, client: CharmmGUIClient):
        self.client = client

    def _save_json_record(self, jobid, params):
        record = {
            "jobid": jobid,
            "module": "Quick Bilayer",
            "submitted_at": datetime.datetime.now().isoformat(),
            "parameters": params
        }
    
        out = os.path.join(JOB_RECORD_DIR, f"{jobid}.json")
        with open(out, "w") as f:
            json.dump(record, f, indent=2)
    
        if not self.client.quiet:
            print(f"📝 Job record saved → {out}")


    def submit(self, **params):
        url = f"{self.client.BASE}/quick_bilayer"

        # Required argument logic
        if not params.get("membrane_only") and not params.get("jobid"):
            raise ValueError("Must provide jobid unless using --membrane-only.")

        if not params.get("membtype"):
            if not (params.get("upper") and params.get("lower")):
                raise ValueError("Must specify membtype OR both upper and lower.")

        # Convert boolean flags to strings
        payload = {}
        for k, v in params.items():
            if v is True:
                payload[k] = "true"
            elif v not in (False, None):
                payload[k] = v

        r = self.client._post(url, data=payload)
        jobid = r.json().get("jobid")

        if not self.client.quiet:
            print(f"🚀 Quick Bilayer submitted → {jobid}")

        # Save job record depending on backend
        if STORAGE_BACKEND == "json":
            self._save_json_record(jobid, params)
        elif STORAGE_BACKEND == "sqlite":
            save_sqlite_record(jobid, params, module="Quick Bilayer")

        return jobid
