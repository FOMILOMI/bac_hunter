from __future__ import annotations
import csv
import html
from datetime import datetime
from typing import Iterable

from ..storage import Storage

class Exporter:
    def __init__(self, db: Storage):
        self.db = db

    def to_csv(self, path: str = "findings.csv"):
        with self.db.conn() as c:
            rows = list(c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC"))
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["base", "type", "url", "evidence", "score"])
            for r in rows:
                w.writerow(r)
        return path

    def to_html(self, path: str = "report.html"):
        with self.db.conn() as c:
            rows = list(c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC"))
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        parts = [
            "<!doctype html><meta charset='utf-8'><title>BAC Hunter Report</title>",
            "<style>body{font-family:system-ui,Segoe UI,Roboto,sans-serif;padding:24px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px}th{background:#f6f6f6;text-align:left}tr:hover{background:#fafafa}</style>",
            f"<h1>BAC Hunter Report</h1><p>Generated {now}</p>",
            "<table><thead><tr><th>#</th><th>Base</th><th>Type</th><th>URL</th><th>Evidence</th><th>Score</th></tr></thead><tbody>"
        ]
        for i, (base, typ, url, ev, score) in enumerate(rows, 1):
            parts.append(
                f"<tr><td>{i}</td><td>{html.escape(base)}</td><td>{html.escape(typ)}</td><td>{html.escape(url)}</td><td>{html.escape(ev)}</td><td>{score:.2f}</td></tr>"
            )
        parts.append("</tbody></table>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(parts))
        return path