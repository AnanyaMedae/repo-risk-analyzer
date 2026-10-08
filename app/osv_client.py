"""Vulnerability evidence from OSV.dev (real public database). Only pinned versions are queried."""
import requests

OSV_BATCH = "https://api.osv.dev/v1/querybatch"


class OsvError(Exception):
    pass


class OsvClient:
    def __init__(self, timeout=20, session=None):
        self.session = session or requests.Session()
        self.timeout = timeout

    def query(self, deps):
        """deps: list of dicts with name/ecosystem/version. Returns list of advisory-ID lists (same order)."""
        if not deps:
            return []
        payload = {"queries": [{"package": {"name": d["name"], "ecosystem": d["ecosystem"]},
                                "version": d["version"]} for d in deps]}
        try:
            r = self.session.post(OSV_BATCH, json=payload, timeout=self.timeout)
            r.raise_for_status()
            results = r.json().get("results", [])
        except (requests.RequestException, ValueError) as exc:
            raise OsvError(f"OSV lookup failed: {exc}") from exc
        if len(results) != len(deps):
            raise OsvError("OSV returned an unexpected number of results")
        return [[v["id"] for v in (res.get("vulns") or [])] for res in results]
