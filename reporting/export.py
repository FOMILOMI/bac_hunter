from __future__ import annotations
import csv
import html
from datetime import datetime
from typing import Iterable, List
import re
import json

from ..storage import Storage

class Exporter:
    def __init__(self, storage: Storage):
        self.db = storage

    def to_csv(self, path: str = "report.csv"):
        with self.db.conn() as c, open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["base", "type", "url", "evidence", "score"])
            for base, t, u, e, s in c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC"):
                w.writerow([base, t, u, self._redact(e), s])
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
        for i, (base, t, u, e, s) in enumerate(rows, start=1):
            parts.append(
                f"<tr><td>{i}</td><td>{self._escape(base)}</td><td>{self._escape(t)}</td><td><a href='{self._escape(u)}' target='_blank'>{self._escape(u)}</a></td><td>{self._escape(self._redact(e))}</td><td>{s:.2f}</td></tr>"
            )
        parts.append("</tbody></table>")
        html_str = "".join(parts)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_str)
        return path

    def to_json(self, path: str = "report.json"):
        with self.db.conn() as c:
            rows = [
                {
                    "base": base,
                    "type": t,
                    "url": u,
                    "evidence": self._redact(e),
                    "score": float(s),
                }
                for (base, t, u, e, s) in c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC")
            ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"generated_at": datetime.utcnow().isoformat() + "Z", "findings": rows}, f, indent=2)
        return path

    def _escape(self, s: str) -> str:
        return (
            (s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&#39;")
        )

    def _redact(self, s: str | None) -> str:
        if not s:
            return ""
        out = s
        # emails
        out = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[redacted-email]", out)
        # JWT-like tokens (header.payload.signature)
        out = re.sub(r"eyJ[\w-]+\.[\w-]+\.[\w-]+", "[redacted-jwt]", out)
        # long digit sequences (>=8)
        out = re.sub(r"\b\d{8,}\b", "[redacted-digits]", out)
        # cookies/session IDs patterns (basic)
        out = re.sub(r"(session|sess|sid|csrftoken|xsrf)[=:\s][^;\s]{8,}", r"\1=[redacted]", out, flags=re.IGNORECASE)
        return out