from __future__ import annotations
import asyncio
import json
import os
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .cli_analysis import SourceCodeAnalyzer
from .command_executor import CommandExecutor
from .models import DiscoveredCommand, ExecuteRequest, ExecuteResponse, RunStatus
from .run_manager import run_manager

# BAC Hunter imports (DB/session exposure)
from bac_hunter.config import Settings
from bac_hunter.storage import Storage
from bac_hunter.session_manager import SessionManager
from bac_hunter.orchestrator import JobStore

app = FastAPI(title="BAC Hunter Web API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static UI if present
_static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="ui")

_analyzer = SourceCodeAnalyzer("/workspace")
_executor = CommandExecutor()
_commands_cache: List[DiscoveredCommand] | None = None


@app.get("/api/commands", response_model=List[DiscoveredCommand])
async def list_commands():
    global _commands_cache
    if _commands_cache is None:
        _commands_cache = _analyzer.analyze()
    return _commands_cache


@app.post("/api/commands/{name}/execute", response_model=ExecuteResponse)
async def execute_command(name: str, req: ExecuteRequest):
    global _commands_cache
    if _commands_cache is None:
        _commands_cache = _analyzer.analyze()
    selected = next((c for c in _commands_cache if c.name == name), None)
    if not selected:
        raise HTTPException(status_code=404, detail="Command not found")

    # Build args to display
    args = _executor.build_cli_args(selected, req.parameters)
    run_id, proc = await _executor.run_stream(selected, req.parameters)
    status = run_manager.create(run_id, selected.name, args)
    status.status = "running"

    async def _pump():
        try:
            assert proc.stdout and proc.stderr
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                run_manager.append(run_id, line)
            err = await proc.stderr.read()
            if err:
                run_manager.append(run_id, err)
            rc = await proc.wait()
            run_manager.complete(run_id, rc)
        except Exception as e:
            run_manager.append(run_id, f"[executor-error] {e}\n".encode())
            run_manager.complete(run_id, 1)

    asyncio.create_task(_pump())
    return ExecuteResponse(run_id=run_id, command=selected.name, args=args)


@app.get("/api/runs", response_model=List[RunStatus])
async def list_runs():
    # simple snapshot
    return list(run_manager._runs.values())


@app.get("/api/runs/{run_id}", response_model=RunStatus)
async def get_run(run_id: str):
    st = run_manager.get(run_id)
    if not st:
        raise HTTPException(status_code=404, detail="Run not found")
    return st


@app.get("/api/runs/{run_id}/logs")
async def get_run_logs(run_id: str, offset: int = 0):
    data = run_manager.read_from(run_id, offset)
    return JSONResponse({"offset": offset + len(data), "data": data.decode(errors="ignore")})


@app.websocket("/ws/runs/{run_id}")
async def ws_run_logs(ws: WebSocket, run_id: str):
    await ws.accept()
    last = 0
    try:
        while True:
            await asyncio.sleep(0.5)
            data = run_manager.read_from(run_id, last)
            if data:
                await ws.send_text(data.decode(errors="ignore"))
                last += len(data)
            st = run_manager.get(run_id)
            if st and st.status in ("completed", "failed", "canceled") and last >= (st.last_log_offset or 0):
                break
    except WebSocketDisconnect:
        return
    except Exception:
        return
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@app.get("/api/db/findings")
async def list_findings(limit: int = 100, offset: int = 0, target: str | None = None):
    s = Settings()
    db = Storage(s.db_path)
    tid = None
    if target:
        tid = db.ensure_target(target)
    rows = db.get_findings(tid, limit=limit, offset=offset)
    return rows


@app.get("/api/db/targets")
async def list_targets():
    s = Settings()
    db = Storage(s.db_path)
    found = []
    with db.conn() as c:
        for row in c.execute("SELECT id, base_url, name FROM targets ORDER BY id DESC"):
            found.append({"id": row[0], "base_url": row[1], "name": row[2]})
    return found


@app.get("/api/sessions/{base}")
async def session_info(base: str):
    s = Settings()
    sm = SessionManager()
    sm.configure(sessions_dir=s.sessions_dir)
    sm.initialize_from_persistent_store()
    return sm.get_session_info(base)


@app.post("/api/orchestrator/enqueue")
async def enqueue_task(job_type: str, target: str, priority: int = 0):
    s = Settings()
    js = JobStore(s.db_path)
    jid = js.enqueue_job(job_type, {"target": target}, priority=priority)
    return {"job_id": jid}


@app.get("/api/orchestrator/status")
async def orchestrator_status():
    s = Settings()
    js = JobStore(s.db_path)
    return js.get_status()


@app.get("/health")
async def health():
    return {"ok": True}