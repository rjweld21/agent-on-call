"""RPC message schemas for orchestrator <-> sub-agent communication."""

import json
from dataclasses import dataclass, asdict


@dataclass
class TaskRequest:
    task_id: str
    description: str
    agent_name: str
    type: str = "task_request"

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class StatusUpdate:
    task_id: str
    status: str  # "working", "waiting_for_input", "done"
    detail: str = ""
    type: str = "status_update"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "StatusUpdate":
        d = json.loads(data)
        return cls(task_id=d["task_id"], status=d["status"], detail=d.get("detail", ""))


@dataclass
class GuidanceRequest:
    task_id: str
    question: str
    context: str = ""
    type: str = "guidance_request"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "GuidanceRequest":
        d = json.loads(data)
        return cls(task_id=d["task_id"], question=d["question"], context=d.get("context", ""))


@dataclass
class GuidanceResponse:
    task_id: str
    answer: str
    type: str = "guidance_response"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "GuidanceResponse":
        d = json.loads(data)
        return cls(task_id=d["task_id"], answer=d["answer"])


@dataclass
class TaskResult:
    task_id: str
    result: str
    status: str  # "done"
    type: str = "task_result"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "TaskResult":
        d = json.loads(data)
        return cls(task_id=d["task_id"], result=d["result"], status=d["status"])
