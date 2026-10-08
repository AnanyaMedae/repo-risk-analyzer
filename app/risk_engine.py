"""Explainable risk scoring. Every point comes from a named factor with a reason and evidence.
Total weights = 100. Higher score = higher risk. Unknown data scores 0 and is labelled unknown."""
from datetime import datetime, timezone

W_MAINT, W_BUS, W_VULN, W_PIN, W_STATUS = 30, 20, 30, 10, 10


def _days_since(iso, now):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (now - dt).days


def _factor(name, points, max_points, reason, evidence=None, known=True):
    return {"name": name, "points": points, "max_points": max_points,
            "reason": reason, "evidence": evidence or [], "known": known}


def score(meta, contributor_counts, deps, osv_ok, advisories, now=None):
    """advisories: dict mapping 'ecosystem:name@version' -> list of OSV IDs."""
    now = now or datetime.now(timezone.utc)
    factors = []

    # 1. Maintenance activity
    pushed = meta.get("pushed_at")
    if pushed:
        d = _days_since(pushed, now)
        pts = 0 if d <= 30 else 5 if d <= 90 else 12 if d <= 180 else 20 if d <= 365 else W_MAINT
        factors.append(_factor("Maintenance activity", pts, W_MAINT, f"Last push {d} days ago.", [f"pushed_at={pushed}"]))
    else:
        factors.append(_factor("Maintenance activity", 0, W_MAINT, "No push date available.", known=False))

    # 2. Bus factor (aggregate only, no identities)
    total = sum(contributor_counts)
    if total > 0:
        share = max(contributor_counts) / total
        pts = W_BUS if share >= 0.8 else 12 if share >= 0.6 else 5 if share >= 0.4 else 0
        factors.append(_factor("Contributor concentration", pts, W_BUS,
                               f"Top contributor made {share:.0%} of commits among {len(contributor_counts)} listed contributors.",
                               [f"top_share={share:.2f}"]))
    else:
        factors.append(_factor("Contributor concentration", 0, W_BUS, "No contributor data available.", known=False))

    # 3. Known vulnerabilities (evidence = OSV IDs)
    pinned = [d for d in deps if d["pinned"]]
    if not osv_ok:
        factors.append(_factor("Known vulnerabilities", 0, W_VULN, "OSV lookup failed; vulnerability status unknown.", known=False))
    elif not pinned:
        factors.append(_factor("Known vulnerabilities", 0, W_VULN, "No pinned dependencies, so no version could be checked.", known=False))
    else:
        vuln_deps = {k: v for k, v in advisories.items() if v}
        pts = min(W_VULN, 10 * len(vuln_deps))
        ev = [f"{k}: {', '.join(v)}" for k, v in sorted(vuln_deps.items())]
        factors.append(_factor("Known vulnerabilities", pts, W_VULN,
                               f"{len(vuln_deps)} of {len(pinned)} pinned dependencies have OSV advisories.", ev))

    # 4. Version pinning
    if deps:
        unpinned = len(deps) - len(pinned)
        pts = round(W_PIN * unpinned / len(deps))
        factors.append(_factor("Unpinned dependencies", pts, W_PIN,
                               f"{unpinned} of {len(deps)} dependencies lack an exact version.", [f"unpinned={unpinned}"]))
    else:
        factors.append(_factor("Unpinned dependencies", 0, W_PIN, "No supported manifest found.", known=False))

    # 5. Repository status
    pts, reasons = 0, []
    if meta.get("archived"):
        pts += W_STATUS
        reasons.append("repository is archived")
    elif (meta.get("open_issues_count") or 0) > 500:
        pts += 5
        reasons.append("more than 500 open issues/PRs")
    factors.append(_factor("Repository status", pts, W_STATUS,
                           "; ".join(reasons).capitalize() + "." if reasons else "Active, no status flags.",
                           [f"archived={bool(meta.get('archived'))}", f"open_issues={meta.get('open_issues_count', 0)}"]))

    total_pts = sum(f["points"] for f in factors)
    level = "low" if total_pts < 25 else "medium" if total_pts < 50 else "high" if total_pts < 75 else "critical"
    unknown = [f["name"] for f in factors if not f["known"]]
    return {"score": total_pts, "max": 100, "level": level, "factors": factors, "unknown_factors": unknown}
