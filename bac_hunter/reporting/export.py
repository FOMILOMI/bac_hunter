from __future__ import annotations
import csv
import html
from datetime import datetime
from typing import Iterable, List, Optional
import re
import json

try:
	from ..storage import Storage
	from ..monitoring.stats_collector import StatsCollector
	from ..recommendations import RecommendationsEngine
except Exception:
	from storage import Storage
	from monitoring.stats_collector import StatsCollector
	from recommendations import RecommendationsEngine

try:
    from jinja2 import Environment, FileSystemLoader  # type: ignore
except Exception:
    Environment = None  # type: ignore
    FileSystemLoader = None  # type: ignore

class Exporter:
    def __init__(self, storage: Storage):
        self.db = storage
        self.reco = RecommendationsEngine()

    def to_csv(self, path: str = "report.csv"):
        with self.db.conn() as c, open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["base", "type", "url", "evidence", "score"])
            for base, t, u, e, s in c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC"):
                w.writerow([base, t, u, self._redact(e), s])
        return path

    def to_html(self, path: str = "report.html", template_dir: Optional[str] = None, template_name: str = ""):
        if template_dir and template_name and Environment and FileSystemLoader:
            try:
                env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
                tpl = env.get_template(template_name)
                with self.db.conn() as c:
                    rows = list(c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC"))
                ctx = {
                    "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "findings": [
                        {"base": base, "type": t, "url": u, "evidence": self._redact(e), "score": float(s)}
                        for (base, t, u, e, s) in rows
                    ],
                }
                html_str = tpl.render(**ctx)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html_str)
                return path
            except Exception:
                # Fallback to default HTML if templating fails
                pass
        with self.db.conn() as c:
            rows = list(c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC"))
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        rec_sections = []
        for (base, t, u, e, s) in rows[:50]:
            tips = self.reco.suggest(t)
            rec_sections.append(f"<details><summary>{self._escape(t)} on {self._escape(u)}</summary><ul>" + "".join(f"<li>{self._escape(x)}</li>" for x in tips) + "</ul></details>")
        parts = [
            "<!doctype html><meta charset='utf-8'><title>BAC Hunter Report</title>",
            "<style>body{font-family:system-ui,Segoe UI,Roboto,sans-serif;padding:24px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px}th{background:#f6f6f6;text-align:left}tr:hover{background:#fafafa}details{margin:8px 0}</style>",
            f"<h1>BAC Hunter Report</h1><p>Generated {now}</p>",
            "<h2>Findings</h2>",
            "<table><thead><tr><th>#</th><th>Base</th><th>Type</th><th>URL</th><th>Evidence</th><th>Score</th></tr></thead><tbody>"
        ]
        for i, (base, t, u, e, s) in enumerate(rows, start=1):
            parts.append(
                f"<tr><td>{i}</td><td>{self._escape(base)}</td><td>{self._escape(t)}</td><td><a href='{self._escape(u)}' target='_blank'>{self._escape(u)}</a></td><td>{self._escape(self._redact(e))}</td><td>{s:.2f}</td></tr>"
            )
        parts.append("</tbody></table>")
        if rec_sections:
            parts.append("<h2>Recommendations</h2>" + "".join(rec_sections))
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
                    "recommendations": self.reco.suggest(t),
                }
                for (base, t, u, e, s) in c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC")
            ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"generated_at": datetime.utcnow().isoformat() + "Z", "findings": rows}, f, indent=2)
        return path

    def to_pdf(self, path: str = "report.pdf"):
        """Generate PDF using WeasyPrint if available; otherwise fallback to HTML and warn."""
        try:
            from weasyprint import HTML  # type: ignore
            html_path = self.to_html("report.tmp.html")
            HTML(filename=html_path).write_pdf(path)
            return path
        except Exception:
            # Fallback: write HTML and let user convert
            return self.to_html(path.replace('.pdf', '.html'))

    def to_sarif(self, path: str = "report.sarif"):
        """Export findings in SARIF v2.1.0 format for CI integrations."""
        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "BAC-HUNTER",
                            "informationUri": "https://example.invalid/bac-hunter",
                            "rules": []
                        }
                    },
                    "results": []
                }
            ]
        }
        rules_index = {}
        with self.db.conn() as c:
            rows = list(c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.score DESC, f.id DESC"))
        for (base, ftype, url, evidence, score) in rows:
            rule_id = f"BH::{ftype}"
            if rule_id not in rules_index:
                rules_index[rule_id] = {
                    "id": rule_id,
                    "name": ftype,
                    "shortDescription": {"text": f"{ftype}"},
                    "help": {"text": "Broken Access Control related finding"}
                }
            level = "none"
            if score >= 0.8:
                level = "error"
            elif score >= 0.5:
                level = "warning"
            else:
                level = "note"
            sarif["runs"][0]["results"].append({
                "ruleId": rule_id,
                "level": level,
                "message": {"text": self._redact(evidence or "")},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": url}
                        }
                    }
                ]
            })
        sarif["runs"][0]["tool"]["driver"]["rules"] = list(rules_index.values())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sarif, f, indent=2)
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