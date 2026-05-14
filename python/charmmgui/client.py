# client.py
import requests
import os
import time

class CharmmGUIClient:
    DEFAULT_BASE = "https://charmm-gui.org/api"
    TOKEN_FILE = os.path.expanduser("~/.charmmgui_token")

    def __init__(self, email=None, password=None, token=None, timeout=10,
                 verbose=False, quiet=False, base_url=None):
        self.email = email
        self.password = password
        self.token = self._resolve_token(token)
        self.timeout = timeout
        self.verbose = verbose
        self.quiet = quiet
        self.BASE = base_url if base_url else self.DEFAULT_BASE

    # -------------------------------------------------------
    # Token helpers
    # -------------------------------------------------------
    @staticmethod
    def _resolve_token(token):
        if token and os.path.exists(os.path.expanduser(token)):
            with open(os.path.expanduser(token)) as f:
                return f.read().strip()
        return token

    def login(self):
        url = f"{self.BASE}/login"
        payload = {"email": self.email, "password": self.password}
        r = requests.post(url, json=payload)
        r.raise_for_status()
        self.token = r.json().get("token")

        if not self.token:
            raise RuntimeError("Login failed (no token returned).")

        if not self.quiet:
            print("✔ Logged in")

        return self.token

    def save_token(self):
        with open(self.TOKEN_FILE, "w") as f:
            f.write(self.token)
        if not self.quiet:
            print(f"🔑 Token saved → {self.TOKEN_FILE}")

    @classmethod
    def load_token(cls):
        candidates = [
            os.path.join(os.getcwd(), "session.token"),
            cls.TOKEN_FILE,
        ]

        for path in candidates:
            if os.path.exists(path):
                with open(path) as f:
                    token = f.read().strip()
                if token:
                    return token

        raise RuntimeError("No saved token found. Run `login` first.")

    def _headers(self):
        if not self.token:
            raise RuntimeError("Token missing. Login or load token first.")
        return {"Authorization": f"Bearer {self.token}"}

    # -------------------------------------------------------
    # GET + POST wrappers with clean error reporting
    # -------------------------------------------------------
    def _post(self, url, data=None):
        r = requests.post(url, headers=self._headers(), data=data)
        if r.status_code >= 400:
            self._print_error(r, url)
        r.raise_for_status()
        return r

    def _get(self, url, stream=False):
        r = requests.get(url, headers=self._headers(), stream=stream)
        if r.status_code >= 400:
            self._print_error(r, url)
        r.raise_for_status()
        return r

    def _print_error(self, response, url):
        if not self.quiet:
            print("====== SERVER ERROR ======")
            print("URL:", url)
            print("Status:", response.status_code)
            print("Response:")
            print(response.text)
            print("==========================")

    # -------------------------------------------------------
    # Status utilities (shared by multiple modules)
    # -------------------------------------------------------
    def status(self, jobid=None):
        if jobid:
            url = f"{self.BASE}/check_status?jobid={jobid}"
        else:
            url = f"{self.BASE}/check_status?check_rq=true"
        r = self._get(url)
        return r.json()

    def poll(self, jobid, interval=None):
        if interval is None:
            interval = self.timeout

        while True:
            st = self.status(jobid)
            if not self.quiet:
                print(f"Status: {st.get('status')} | Modified: {st.get('last_modified')}")

            if st.get("status") == "done":
                if not self.quiet:
                    print("🎉 Job complete")
                return st

            if st.get("status") == "error":
                raise RuntimeError("Job failed.")

            time.sleep(interval)

    # ---------------- DOWNLOAD ----------------
    def download(self, jobid, outfile="charmm-gui.tgz"):
        url = f"{self.BASE}/download?jobid={jobid}"
        r = requests.get(url, headers=self._headers(), stream=True)

        ctype = r.headers.get("Content-Type", "")
        if "application" in ctype:    # .tgz binary file
            with open(outfile, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            print(f"📦 Downloaded → {outfile}")
            return outfile

        print(f"⚠ File not ready — server says:\n{r.text}")
        return None
    # ------------------------------------------------------
