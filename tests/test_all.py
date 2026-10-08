"""Unit tests. Fakes are used ONLY here to isolate logic; the running app uses the real APIs."""
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.dependencies import parse_package_json, parse_requirements
from app.main import create_app, parse_repo
from app.osv_client import OsvError
from app.risk_engine import score
from app.service import analyze
from app.store import Store

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeGitHub:
    def get_repo(self, o, n):
        return {"pushed_at": "2025-12-20T00:00:00Z", "archived": False, "open_issues_count": 3,
                "stargazers_count": 10, "forks_count": 1, "language": "Python", "license": {"spdx_id": "MIT"}}

    def get_contributor_commit_counts(self, o, n):
        return [90, 5, 5]

    def get_file_text(self, o, n, path):
        return "flask==1.0\nrequests>=2\n" if path == "requirements.txt" else None


class FakeOsv:
    def query(self, deps):
        return [["GHSA-xxxx"] for _ in deps]


class BadOsv:
    def query(self, deps):
        raise OsvError("down")


class DependencyTests(unittest.TestCase):
    def test_requirements(self):
        d = parse_requirements("flask==1.0  # c\nrequests>=2.0\n-r other.txt\nnumpy\n")
        self.assertEqual([x["name"] for x in d], ["flask", "requests", "numpy"])
        self.assertEqual([x["pinned"] for x in d], [True, False, False])
        self.assertEqual(d[0]["version"], "1.0")

    def test_package_json(self):
        d = parse_package_json('{"dependencies":{"a":"1.2.3","b":"^2.0.0"}}')
        self.assertEqual([x["pinned"] for x in d], [True, False])

    def test_bad_json(self):
        self.assertEqual(parse_package_json("{oops"), [])


class RiskTests(unittest.TestCase):
    def test_healthy_repo_low(self):
        meta = {"pushed_at": "2025-12-25T00:00:00Z", "archived": False, "open_issues_count": 1}
        r = score(meta, [10, 10, 10, 10], [], True, {}, now=NOW)
        self.assertEqual(r["level"], "low")

    def test_vulnerability_evidence_required(self):
        deps = [{"name": "x", "ecosystem": "PyPI", "version": "1", "pinned": True}]
        r = score({"pushed_at": "2025-12-25T00:00:00Z"}, [1], deps, True, {"PyPI:x@1": ["GHSA-1"]}, now=NOW)
        vf = [f for f in r["factors"] if f["name"] == "Known vulnerabilities"][0]
        self.assertEqual(vf["points"], 10)
        self.assertIn("GHSA-1", vf["evidence"][0])

    def test_osv_failure_is_unknown_not_zero_claim(self):
        deps = [{"name": "x", "ecosystem": "PyPI", "version": "1", "pinned": True}]
        r = score({"pushed_at": "2025-12-25T00:00:00Z"}, [1], deps, False, {}, now=NOW)
        self.assertIn("Known vulnerabilities", r["unknown_factors"])

    def test_abandoned_archived_is_high(self):
        meta = {"pushed_at": "2020-01-01T00:00:00Z", "archived": True, "open_issues_count": 0}
        r = score(meta, [100, 1], [], True, {}, now=NOW)
        self.assertGreaterEqual(r["score"], 50)


class ServiceAndApiTests(unittest.TestCase):
    def test_service(self):
        res = analyze("o", "n", FakeGitHub(), FakeOsv())
        self.assertEqual(res["dependencies"]["pinned"], 1)
        self.assertEqual(res["vulnerability_source"], "OSV.dev")
        self.assertNotIn("login", str(res))

    def test_service_osv_down(self):
        res = analyze("o", "n", FakeGitHub(), BadOsv())
        self.assertEqual(res["vulnerability_source"], "unavailable")

    def test_parse_repo(self):
        self.assertEqual(parse_repo("https://github.com/pallets/flask.git"), ("pallets", "flask"))
        with self.assertRaises(ValueError):
            parse_repo("nonsense")

    def test_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(FakeGitHub(), FakeOsv(), Store(str(Path(tmp) / "t.db")))
            c = app.test_client()
            self.assertEqual(c.get("/healthz").status_code, 200)
            self.assertEqual(c.get("/api/analyze?repo=bad").status_code, 400)
            self.assertEqual(c.get("/api/analyze?repo=o/n").status_code, 200)
            self.assertEqual(len(c.get("/api/history").get_json()), 1)
            self.assertEqual(c.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
