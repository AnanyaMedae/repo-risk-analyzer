"""Thin client for the real GitHub REST API. No fake responses."""
import requests


class GitHubError(Exception):
    pass


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token=None, timeout=15, session=None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repo-risk-analyzer",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.timeout = timeout

    def _get(self, path, params=None, headers=None, allow_404=False):
        try:
            r = self.session.get(self.BASE + path, params=params, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise GitHubError(f"Network error talking to GitHub: {exc}") from exc
        if r.status_code == 404:
            if allow_404:
                return None
            raise GitHubError("Repository not found (or it is private).")
        if r.status_code in (403, 429) and r.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubError("GitHub rate limit exceeded. Set GITHUB_TOKEN in .env.")
        if not r.ok:
            raise GitHubError(f"GitHub API error {r.status_code}")
        return r

    def get_repo(self, owner, name):
        return self._get(f"/repos/{owner}/{name}").json()

    def get_contributor_commit_counts(self, owner, name):
        """Return only anonymous commit counts per contributor (no logins are kept)."""
        r = self._get(f"/repos/{owner}/{name}/contributors", params={"per_page": 100}, allow_404=True)
        if r is None or r.status_code != 200:
            return []
        return [c.get("contributions", 0) for c in r.json()]

    def get_file_text(self, owner, name, path):
        r = self._get(f"/repos/{owner}/{name}/contents/{path}",
                      headers={"Accept": "application/vnd.github.raw+json"}, allow_404=True)
        return r.text if r is not None else None
