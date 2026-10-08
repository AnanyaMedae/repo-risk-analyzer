"""Orchestrates ingestion -> dependency analysis -> vulnerability evidence -> risk score."""
from datetime import datetime, timezone

from .dependencies import MANIFESTS, parse_manifest
from .osv_client import OsvError
from .risk_engine import score


def analyze(owner, name, github, osv):
    meta = github.get_repo(owner, name)
    counts = github.get_contributor_commit_counts(owner, name)

    deps, found = [], []
    for fn in MANIFESTS:
        text = github.get_file_text(owner, name, fn)
        if text is not None:
            found.append(fn)
            deps.extend(parse_manifest(fn, text))

    pinned = [d for d in deps if d["pinned"]]
    advisories, osv_ok = {}, True
    try:
        results = osv.query(pinned)
        for d, ids in zip(pinned, results):
            d["advisories"] = ids
            advisories[f"{d['ecosystem']}:{d['name']}@{d['version']}"] = ids
    except OsvError:
        osv_ok = False

    risk = score(meta, counts, deps, osv_ok, advisories)
    return {
        "repo": f"{owner}/{name}",
        "analyzed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metadata": {"stars": meta.get("stargazers_count"), "forks": meta.get("forks_count"),
                     "open_issues": meta.get("open_issues_count"), "archived": meta.get("archived"),
                     "language": meta.get("language"), "pushed_at": meta.get("pushed_at"),
                     "license": (meta.get("license") or {}).get("spdx_id")},
        "dependencies": {"manifests": found, "total": len(deps), "pinned": len(pinned), "items": deps},
        "vulnerability_source": "OSV.dev" if osv_ok else "unavailable",
        "risk": risk,
    }
