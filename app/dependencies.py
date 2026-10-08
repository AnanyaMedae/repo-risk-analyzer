"""Parse dependency manifests. Only exact (pinned) versions are treated as 'known'."""
import json
import re

_REQ = re.compile(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*(==|>=|<=|~=|!=|>|<)?\s*([^\s;#,]+)?")
_EXACT_NPM = re.compile(r"^\d+\.\d+\.\d+([\-+][0-9A-Za-z.\-+]*)?$")

MANIFESTS = ("requirements.txt", "package.json")


def parse_requirements(text):
    deps = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            continue
        m = _REQ.match(line)
        if not m:
            continue
        name, op, ver = m.groups()
        pinned = op == "==" and bool(ver) and "*" not in ver
        deps.append({"name": name, "ecosystem": "PyPI", "version": ver if pinned else None,
                     "declared": f"{op or ''}{ver or ''}", "pinned": pinned, "manifest": "requirements.txt"})
    return deps


def parse_package_json(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    deps = []
    for name, spec in (data.get("dependencies") or {}).items():
        spec = str(spec).strip()
        pinned = bool(_EXACT_NPM.match(spec))
        deps.append({"name": name, "ecosystem": "npm", "version": spec if pinned else None,
                     "declared": spec, "pinned": pinned, "manifest": "package.json"})
    return deps


def parse_manifest(filename, text):
    if filename == "requirements.txt":
        return parse_requirements(text)
    if filename == "package.json":
        return parse_package_json(text)
    return []
