from __future__ import annotations
import asyncio
from typing import List, Dict, Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse

try:
    from ..config import Settings
    from ..storage import Storage
    from ..http_client import HttpClient
    from ..monitoring.stats_collector import StatsCollector
    from ..reporting import Exporter
    from ..plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, SmartEndpointDetector
except Exception:
    from config import Settings
    from storage import Storage
    from http_client import HttpClient
    from monitoring.stats_collector import StatsCollector
    from reporting import Exporter
    from plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, SmartEndpointDetector

app = FastAPI(title="BAC Hunter Dashboard", version="1.0")

_stats = StatsCollector()
_settings = Settings()
_db = Storage(_settings.db_path)

@app.get("/")
async def index():
	# Minimal HTML index for quick usage
	html = """
	<!doctype html>
	<meta charset='utf-8'>
	<title>BAC Hunter Dashboard</title>
	<style>
	body{font-family:system-ui,Segoe UI,Roboto,sans-serif;padding:20px}
	input,button,select{padding:6px;margin:4px}
	table{border-collapse:collapse;width:100%}
	th,td{border:1px solid #ddd;padding:8px}
	th{background:#f6f6f6;text-align:left}
	</style>
	<h1>BAC Hunter</h1>
	<div>
		<input id='target' placeholder='https://target.com' style='width:320px'/>
		<button onclick='runScan()'>Run Quick Scan</button>
		<input id='q' placeholder='filter'/>
		<select id='sort'>
			<option value='score'>score</option>
			<option value='type'>type</option>
		</select>
		<select id='order'>
			<option value='desc'>desc</option>
			<option value='asc'>asc</option>
		</select>
		<button onclick='loadFindings()'>Refresh</button>
		<a href='/api/export/html' target='_blank'>HTML</a>
		<a href='/api/export/csv' target='_blank'>CSV</a>
		<a href='/api/export/json' target='_blank'>JSON</a>
	</div>
	<pre id='stats'></pre>
	<table id='tbl'><thead><tr><th>Score</th><th>Type</th><th>URL</th><th>Evidence</th></tr></thead><tbody></tbody></table>
	<script>
	async function loadStats(){
	 const r = await fetch('/api/stats');
	 const j = await r.json();
	 document.getElementById('stats').textContent = JSON.stringify(j, null, 2);
	}
	async function loadFindings(){
	 const q = document.getElementById('q').value;
	 const sort = document.getElementById('sort').value;
	 const order = document.getElementById('order').value;
	 const r = await fetch(`/api/findings?q=${encodeURIComponent(q)}&sort=${sort}&order=${order}`);
	 const j = await r.json();
	 const tbody = document.querySelector('#tbl tbody');
	 tbody.innerHTML='';
	 for (const it of j.items){
	   const tr = document.createElement('tr');
	   tr.innerHTML = `<td>${Number(it.score).toFixed(2)}</td><td>${it.type}</td><td><a href='${it.url}' target='_blank'>${it.url}</a></td><td>${it.evidence}</td>`;
	   tbody.appendChild(tr);
	 }
	}
	async function runScan(){
	 const t = document.getElementById('target').value;
	 if(!t) return;
	 await fetch(`/api/scan?target=${encodeURIComponent(t)}`, {method:'POST'});
	 await loadFindings();
	}
	loadStats();
	loadFindings();
	</script>
	"""
	return HTMLResponse(content=html)

@app.get("/api/stats")
async def get_stats():
	return JSONResponse(_stats.get_summary())

@app.get("/api/findings")
async def list_findings(q: str | None = None, sort: str = "score", order: str = "desc"):
	with _db.conn() as c:
		rows = list(c.execute("SELECT t.base_url, f.type, f.url, f.evidence, f.score FROM findings f JOIN targets t ON f.target_id=t.id ORDER BY f.id DESC"))
		items = [
			{"base": base, "type": t, "url": u, "evidence": e, "score": float(s)} for (base, t, u, e, s) in rows
		]
		if q:
			q_lower = q.lower()
			items = [x for x in items if q_lower in x["url"].lower() or q_lower in x["type"].lower()]
		# Sort client-side for simplicity
		key = (sort or "score")
		reverse = (order or "desc").lower() != "asc"
		items.sort(key=lambda x: x.get(key, 0), reverse=reverse)
		return JSONResponse({"items": items})

@app.post("/api/scan")
async def run_scan(target: str = Query(..., description="Target base URL")):
	settings = Settings()
	settings.targets = [target]
	http = HttpClient(settings)
	try:
		for base in settings.targets:
			tid = _db.ensure_target(base)
			plugins = [RobotsRecon(settings, http, _db), SitemapRecon(settings, http, _db), JSEndpointsRecon(settings, http, _db), SmartEndpointDetector(settings, http, _db)]
			for p in plugins:
				try:
					await p.run(base, tid)
				except Exception:
					pass
	finally:
		await http.close()
	return JSONResponse({"ok": True})

@app.get("/api/export/{fmt}")
async def export(fmt: str):
	ex = Exporter(_db)
	if fmt == "csv":
		path = ex.to_csv("web-report.csv")
		return FileResponse(path, filename="report.csv")
	elif fmt == "json":
		path = ex.to_json("web-report.json")
		return FileResponse(path, filename="report.json")
	elif fmt == "pdf":
		path = ex.to_pdf("web-report.pdf")
		# If fallback produced HTML, still return that
		name = "report.pdf" if path.endswith(".pdf") else "report.html"
		return FileResponse(path, filename=name)
	else:
		path = ex.to_html("web-report.html")
		return FileResponse(path, filename="report.html")