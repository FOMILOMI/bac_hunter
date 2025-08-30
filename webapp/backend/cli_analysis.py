from __future__ import annotations
import ast
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .models import DiscoveredCommand, Parameter


@dataclass
class _ParamInfo:
    name: str
    kind: str  # argument|option
    type_str: str
    required: bool
    default: Any
    help_text: Optional[str]
    flags: List[str]


class SourceCodeAnalyzer:
    def __init__(self, repo_root: str = "/workspace"):
        self.repo_root = repo_root
        self.cli_path = os.path.join(repo_root, "bac_hunter", "cli.py")

    def analyze(self) -> List[DiscoveredCommand]:
        with open(self.cli_path, "r", encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src)
        commands: List[DiscoveredCommand] = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                cmd_name = self._extract_command_name(node)
                if not cmd_name:
                    continue
                params: List[Parameter] = []
                for arg in node.args.args:
                    if arg.arg == "ctx":
                        # Typer context parameter
                        continue
                    pinf = self._parse_param_for(node, arg)
                    if pinf:
                        params.append(
                            Parameter(
                                name=pinf.name,
                                kind=pinf.kind, type=pinf.type_str, required=pinf.required,
                                default=pinf.default, help=pinf.help_text, flags=pinf.flags,
                            )
                        )
                help_text = ast.get_docstring(node)
                commands.append(
                    DiscoveredCommand(
                        name=cmd_name,
                        function_name=node.name,
                        module="bac_hunter.cli",
                        parameters=params,
                        help=help_text,
                        dependencies=[],
                        output_format="text",
                    )
                )
        return commands

    def _extract_command_name(self, fn: ast.FunctionDef) -> Optional[str]:
        # Look for @app.command(...)
        for deco in fn.decorator_list:
            if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                if deco.func.attr == "command" and isinstance(deco.func.value, ast.Name) and deco.func.value.id == "app":
                    # name kwarg if provided
                    for kw in deco.keywords or []:
                        if kw.arg == "name":
                            try:
                                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                    return kw.value.value
                            except Exception:
                                pass
                    # default: function name with underscores converted to dashes
                    return fn.name.replace("_", "-")
            if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name) and deco.func.id == "app":
                # uncommon, skip
                continue
        # Also include callback (top-level, not a command)
        return None

    def _annotation_to_type(self, ann: Optional[ast.expr]) -> str:
        if ann is None:
            return "string"
        try:
            if isinstance(ann, ast.Subscript) and isinstance(ann.value, ast.Name) and ann.value.id in ("List", "list"):
                elt = ann.slice
                if isinstance(elt, ast.Name):
                    return f"array<{elt.id.lower()}>"
                if isinstance(elt, ast.Subscript) and isinstance(elt.value, ast.Name):
                    return f"array<{elt.value.id.lower()}>"
                return "array<string>"
            if isinstance(ann, ast.Name):
                t = ann.id.lower()
                if t in ("int", "float", "bool", "str"):
                    return {"int": "integer", "float": "number", "bool": "boolean", "str": "string"}[t]
                return "string"
        except Exception:
            pass
        return "string"

    def _parse_param_for(self, fn: ast.FunctionDef, arg: ast.arg) -> Optional[_ParamInfo]:
        name = arg.arg
        type_str = self._annotation_to_type(arg.annotation)
        default = None
        required = False
        kind = "argument"
        help_text: Optional[str] = None
        flags: List[str] = []

        # Find default via function defaults
        # Map arg position to default
        pos_args = [a.arg for a in fn.args.args]
        defaults = fn.args.defaults or []
        default_map: Dict[str, ast.expr] = {}
        if defaults:
            # Defaults align to last N positional args
            for idx, d in enumerate(defaults, start=len(pos_args) - len(defaults)):
                default_map[pos_args[idx]] = d

        if name not in default_map:
            # No default => required argument
            required = True
            return _ParamInfo(name=name, kind=kind, type_str=type_str, required=required, default=None, help_text=help_text, flags=flags)

        dnode = default_map[name]
        # Detect typer.Argument/Option
        if isinstance(dnode, ast.Call) and isinstance(dnode.func, ast.Attribute):
            if isinstance(dnode.func.value, ast.Name) and dnode.func.value.id == "typer":
                callee = dnode.func.attr
                if callee == "Argument":
                    kind = "argument"
                    # First arg can be Ellipsis (required)
                    if dnode.args:
                        if isinstance(dnode.args[0], ast.Name) and dnode.args[0].id == "Ellipsis":
                            required = True
                            default = None
                        elif isinstance(dnode.args[0], ast.Constant):
                            default = dnode.args[0].value
                    for kw in dnode.keywords or []:
                        if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                            help_text = str(kw.value.value)
                elif callee == "Option":
                    kind = "option"
                    # First arg is default value
                    if dnode.args:
                        if isinstance(dnode.args[0], ast.Constant):
                            default = dnode.args[0].value
                        elif isinstance(dnode.args[0], ast.Name) and dnode.args[0].id == "None":
                            default = None
                    for a in dnode.args[1:]:
                        if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value.startswith("-"):
                            flags.append(a.value)
                    for kw in dnode.keywords or []:
                        if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                            help_text = str(kw.value.value)
                    required = False
                else:
                    # treat as plain default
                    pass
        else:
            # Plain default constant
            if isinstance(dnode, ast.Constant):
                default = dnode.value
            required = False

        return _ParamInfo(name=name, kind=kind, type_str=type_str, required=required, default=default, help_text=help_text, flags=flags)