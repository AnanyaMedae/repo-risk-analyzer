"""Flask app: dashboard + JSON API.  Run with:  python -m app.main"""
import re

from flask import Flask, jsonify, render_template, request

from . import config
from .github_client import GitHubClient, GitHubError
from .osv_client import OsvClient
from .service import analyze
from .store import Store

_PART = re.compile(r"^[A-Za-z0-9_.\-]+$")


def parse_repo(text):
    text = (text or "").strip()
    text = re.sub(r"^https?://github\.com/", "", text).removesuffix(".git").strip("/")
    parts = text.split("/")
    if len(parts) < 2 or not _PART.match(parts[0]) or not _PART.match(parts[1]):
        raise ValueError("Use the form owner/name or a github.com URL.")
    return parts[0], parts[1]


def create_app(github=None, osv=None, store=None):
    app = Flask(__name__)
    github = github or GitHubClient(token=config.GITHUB_TOKEN)
    osv = osv or OsvClient()
    store = store or Store(config.DB_PATH)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/healthz")
    def health():
        return jsonify(status="ok")

    @app.get("/api/analyze")
    def api_analyze():
        try:
            owner, name = parse_repo(request.args.get("repo"))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        try:
            result = analyze(owner, name, github, osv)
        except GitHubError as exc:
            return jsonify(error=str(exc)), 502
        store.save(result)
        return jsonify(result)

    @app.get("/api/history")
    def history():
        return jsonify(store.recent())

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=config.PORT)
