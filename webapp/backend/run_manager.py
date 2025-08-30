from __future__ import annotations
import asyncio
import time
from typing import Dict, Optional

from models import RunStatus


class RunManager:
    def __init__(self):
        self._runs: Dict[str, RunStatus] = {}
        self._buffers: Dict[str, bytearray] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    def create(self, run_id: str, command: str, args: list[str]) -> RunStatus:
        rs = RunStatus(id=run_id, command=command, args=args, status="pending", started_at=time.time())
        self._runs[run_id] = rs
        self._buffers[run_id] = bytearray()
        return rs

    def get(self, run_id: str) -> Optional[RunStatus]:
        return self._runs.get(run_id)

    def append(self, run_id: str, data: bytes):
        if run_id in self._buffers:
            self._buffers[run_id].extend(data)
            r = self._runs.get(run_id)
            if r:
                r.last_log_offset = len(self._buffers[run_id])

    def read_from(self, run_id: str, offset: int) -> bytes:
        buf = self._buffers.get(run_id, bytearray())
        return bytes(buf[offset:])

    def set_task(self, run_id: str, task: asyncio.Task):
        self._tasks[run_id] = task

    def complete(self, run_id: str, rc: int):
        if run_id in self._runs:
            rs = self._runs[run_id]
            rs.status = "completed" if rc == 0 else "failed"
            rs.return_code = rc
            rs.ended_at = time.time()


run_manager = RunManager()