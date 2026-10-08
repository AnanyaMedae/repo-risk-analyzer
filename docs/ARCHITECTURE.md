# Architecture

Browser dashboard -> Flask API -> service layer
service: GitHubClient (real GitHub REST) -> dependency parsers -> OsvClient (real OSV.dev) -> risk_engine -> SQLite history

## Design decisions
- Single deployable service. No microservices: nothing here needs independent scaling yet.
- No AI/ML. The score is a transparent rule set (100 points: maintenance 30, vulnerabilities 30,
  contributor concentration 20, unpinned deps 10, repo status 10). Each factor returns reason + evidence.
- A vulnerability is only reported with an OSV advisory ID. Only exact pinned versions are queried.
  If OSV fails, the factor is marked "unknown" instead of "safe".
- Privacy: contributor logins are never stored or returned; only anonymous commit-count shares are used.
- Secrets: GITHUB_TOKEN comes from environment/.env (git-ignored).

## Known limitations
- Only requirements.txt and package.json at the repo root. Lock files (package-lock.json, poetry.lock) would give
  resolved versions and are the best next step.
- Contributors endpoint is limited to the first 100 contributors.
- Score thresholds are heuristics; tune them against your own data before relying on them.

## Deferred (not built, by design)
Kafka (needed only for async/bulk ingestion), Kubernetes (manifest provided as a starting point).
