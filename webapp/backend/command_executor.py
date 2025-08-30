from __future__ import annotations
import asyncio
import json
import shlex
import sys
import uuid
from typing import Any, Dict, List, Tuple

from .models import DiscoveredCommand


class CommandExecutor:
    def __init__(self, python_executable: str = sys.executable):
        self.python = python_executable

    def build_cli_args(self, command: DiscoveredCommand, param_values: Dict[str, Any]) -> List[str]:
        args: List[str] = ["-m", "bac_hunter.cli", command.name]
        # Build mapping name->Parameter
        param_index = {p.name: p for p in command.parameters}
        # Maintain original declaration order
        for p in command.parameters:
            if p.kind == "argument":
                if p.name in param_values:
                    v = param_values[p.name]
                    if isinstance(v, list):
                        args.extend([str(x) for x in v])
                    else:
                        args.append(str(v))
                elif p.required and p.default is None:
                    raise ValueError(f"Missing required argument: {p.name}")
        # Options next
        for p in command.parameters:
            if p.kind != "option":
                continue
            if p.name not in param_values:
                # Only include if boolean with default True and requested to flip? skip unless provided
                continue
            v = param_values[p.name]
            opt = f"--{p.name.replace('_','-')}"
            # Handle booleans as --flag/--no-flag
            if isinstance(v, bool):
                if v:
                    args.append(opt)
                else:
                    args.append(f"--no-{p.name.replace('_','-')}")
            elif isinstance(v, list):
                # Join by comma for list options
                args.append(opt)
                args.append(",".join([str(x) for x in v]))
            else:
                args.append(opt)
                args.append(str(v))
        return args

    async def run_stream(self, command: DiscoveredCommand, params: Dict[str, Any]) -> Tuple[str, asyncio.subprocess.Process]:
        run_id = uuid.uuid4().hex
        args = self.build_cli_args(command, params)
        proc = await asyncio.create_subprocess_exec(
            self.python, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return run_id, proc

    async def run_collect(self, command: DiscoveredCommand, params: Dict[str, Any]) -> Tuple[int, str, str]:
        args = self.build_cli_args(command, params)
        proc = await asyncio.create_subprocess_exec(
            self.python, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        return proc.returncode or 0, (out or b"").decode(), (err or b"").decode()