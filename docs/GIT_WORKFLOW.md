# Git workflow
Branches: main (stable), develop (integration), feature/* (one per phase).

## One-time setup
git init -b main
git add .
git commit -m "chore: initial project skeleton"
git checkout -b develop

## Phase 1 - feature/github-ingestion
git checkout -b feature/github-ingestion develop
git add app/config.py app/github_client.py
git commit -m "feat(ingestion): add GitHub REST client with rate-limit handling"
git push -u origin feature/github-ingestion
PR title: feat: GitHub ingestion client
PR description: Adds a real GitHub API client (metadata, anonymous contributor counts, manifest files). No contributor identities stored.

## Phase 2 - feature/dependency-analysis
git checkout -b feature/dependency-analysis develop
git add app/dependencies.py app/osv_client.py
git commit -m "feat(deps): parse requirements.txt/package.json and query OSV.dev"
git push -u origin feature/dependency-analysis
PR title: feat: dependency parsing and OSV evidence
PR description: Parses manifests, queries OSV only for pinned versions, returns advisory IDs as evidence.

## Phase 3 - feature/risk-engine
git checkout -b feature/risk-engine develop
git add app/risk_engine.py app/service.py tests/
git commit -m "feat(risk): explainable 100-point risk engine with tests"
git push -u origin feature/risk-engine
PR title: feat: explainable risk engine
PR description: Five weighted factors, each with reason and evidence; unknown data is labelled unknown.

## Phase 4 - feature/dashboard
git checkout -b feature/dashboard develop
git add app/main.py app/store.py app/templates/
git commit -m "feat(dashboard): Flask API, SQLite history and web dashboard"
git push -u origin feature/dashboard
PR title: feat: dashboard and API
PR description: Adds /api/analyze, /api/history and a single-page dashboard.

## Optional later phases
feature/kafka (async bulk ingestion), feature/kubernetes (k8s/ + Dockerfile)
git commit -m "feat(k8s): add Dockerfile and Kubernetes manifest"

Merge each feature into develop via PR, then develop -> main after tests pass.
