from __future__ import annotations
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class Parameter(BaseModel):
    name: str
    kind: Literal["argument", "option"] = "argument"
    type: str = "string"
    required: bool = False
    default: Any | None = None
    help: Optional[str] = None
    flags: List[str] = Field(default_factory=list)


class DiscoveredCommand(BaseModel):
    name: str
    function_name: str
    module: str
    help: Optional[str] = None
    parameters: List[Parameter] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    output_format: Optional[str] = None


class ExecuteRequest(BaseModel):
    parameters: Dict[str, Any] = Field(default_factory=dict)
    stream: bool = True


class ExecuteResponse(BaseModel):
    run_id: str
    command: str
    args: List[str]


class RunStatus(BaseModel):
    id: str
    command: str
    args: List[str]
    status: Literal["pending", "running", "completed", "failed", "canceled"]
    return_code: Optional[int] = None
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    last_log_offset: int = 0


class Finding(BaseModel):
    id: int
    target_id: int
    type: str
    url: str
    evidence: Optional[str] = None
    score: float
    severity: Optional[str] = None
    status: Optional[str] = None


class Target(BaseModel):
    id: int
    base_url: str
    name: Optional[str] = None