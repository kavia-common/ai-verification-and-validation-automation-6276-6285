from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Job:
    id: str
    created_at: str
    status: str
    paths: Dict[str, str]
    srs: Dict[str, str]
    cases_count: Optional[int] = None
    scripts_count: Optional[int] = None


@dataclass
class Run:
    id: str
    jobId: str
    created_at: str
    status: str
    duration: float
    totals: Dict[str, int]
    artifacts_dir: str


@dataclass
class Report:
    runId: str
    jobId: str
    created_at: str
    status: str
    duration: float
    totals: Dict[str, int]
