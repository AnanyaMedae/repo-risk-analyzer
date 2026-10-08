# Repo Risk Analyzer

Analyzes a public GitHub repository and produces an explainable 0-100 risk score using real GitHub data
and OSV.dev vulnerability advisories. See docs/ARCHITECTURE.md.

## Run in Visual Studio Code (Windows)
1. Install Python 3.10+ (tick "Add to PATH") and VS Code with the Python extension.
2. Unzip, then File > Open Folder > repo-risk-analyzer.
3. Terminal > New Terminal (PowerShell):
       python -m venv .venv
       .venv\Scripts\Activate.ps1
       pip install -r requirements.txt
       copy .env.example .env
   (If activation is blocked: Set-ExecutionPolicy -Scope Process Bypass)
4. Edit .env and paste a GitHub token after GITHUB_TOKEN= (optional, avoids rate limits).
5. Run:  python -m app.main     (or press F5 and choose "Run Repo Risk Analyzer")
6. Open http://127.0.0.1:5000 and analyze e.g. pallets/flask.

macOS/Linux: use `python3 -m venv .venv && source .venv/bin/activate` and `cp .env.example .env`.

## Tests
    python -m unittest discover -s tests -v
Expected: "Ran 11 tests ... OK".

## API
    GET /api/analyze?repo=owner/name
    GET /api/history
    GET /healthz

## Common errors
- "GitHub rate limit exceeded": set GITHUB_TOKEN in .env, restart.
- "Repository not found": private repo or typo.
- ModuleNotFoundError: run commands from the project root with the venv active.
- Port in use: set PORT=5001 in .env.
