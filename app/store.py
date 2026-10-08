"""SQLite history of analyses (stdlib only)."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS analyses(
                id INTEGER PRIMARY KEY AUTOINCREMENT, repo TEXT, analyzed_at TEXT,
                score INTEGER, level TEXT, result TEXT)""")

    @contextmanager
    def _conn(self):
        connection = sqlite3.connect(self.path)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def save(self, result):
        with self._conn() as c:
            c.execute("INSERT INTO analyses(repo,analyzed_at,score,level,result) VALUES(?,?,?,?,?)",
                      (result["repo"], result["analyzed_at"], result["risk"]["score"],
                       result["risk"]["level"], json.dumps(result)))

    def recent(self, limit=10):
        with self._conn() as c:
            rows = c.execute("SELECT repo,analyzed_at,score,level FROM analyses ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"repo": r[0], "analyzed_at": r[1], "score": r[2], "level": r[3]} for r in rows]
