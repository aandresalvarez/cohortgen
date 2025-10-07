"""
Data models for UI run management.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class RunStatus(str, Enum):
    """Status of a cohort run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(str, Enum):
    """Status of an individual stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    WAITING_FOR_INPUT = "waiting_for_input"  # For interactive Stage 1


@dataclass
class ChatMessage:
    """A message in the Stage 1 clarification chat."""

    role: str  # "assistant" or "user"
    content: str


@dataclass
class ClarificationSession:
    """State for an interactive Stage 1 clarification session."""

    run_id: str
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    is_complete: bool = False
    cohort_definition: Optional[dict[str, Any]] = None


@dataclass
class StageMetrics:
    """Metrics for a single stage."""

    duration_seconds: float = 0.0
    llm_calls: int = 0
    athena_calls: int = 0
    concepts_found: int = 0
    error_message: str = ""


@dataclass
class StageResult:
    """Result from a stage execution."""

    stage: int
    status: StageStatus
    started_at: str
    completed_at: Optional[str] = None
    metrics: StageMetrics = field(default_factory=StageMetrics)
    artifact_path: Optional[str] = None


@dataclass
class UserInputs:
    """User inputs for a cohort run."""

    cohort_description: str
    # Stage 2 knobs
    max_concept_sets: int = 5
    max_queries_per_set: int = 3
    search_top_k: int = 10
    per_set_time_limit_sec: int = 30
    max_accepted_per_set: int = 5
    # BigQuery config
    bigquery_project_id: str = ""
    omop_dataset_id: str = ""
    bigquery_location: str = "US"
    # Fast mode
    fast_mode: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserInputs":
        """Create from dict."""
        return cls(**data)


@dataclass
class CohortRun:
    """A complete cohort generation run."""

    run_id: str
    name: str
    created_at: str
    status: RunStatus
    user_inputs: UserInputs
    stages: list[StageResult] = field(default_factory=list)
    error: str = ""
    total_duration_seconds: float = 0.0

    # Stage 1 interactive session
    clarification_session: Optional[ClarificationSession] = None

    # Artifact paths
    stage1_path: Optional[str] = None
    stage1_log_path: Optional[str] = None
    stage2_path: Optional[str] = None
    stage2_log_path: Optional[str] = None
    stage3_sql_path: Optional[str] = None
    stage3_log_path: Optional[str] = None
    stage3_validation_path: Optional[str] = None
    stage4_path: Optional[str] = None
    log_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "run_id": self.run_id,
            "name": self.name,
            "created_at": self.created_at,
            "status": self.status.value,
            "user_inputs": self.user_inputs.to_dict(),
            "stages": [
                {
                    "stage": s.stage,
                    "status": s.status.value,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "metrics": asdict(s.metrics),
                    "artifact_path": s.artifact_path,
                }
                for s in self.stages
            ],
            "error": self.error,
            "total_duration_seconds": self.total_duration_seconds,
            "clarification_session": (
                asdict(self.clarification_session) if self.clarification_session else None
            ),
            "stage1_path": self.stage1_path,
            "stage1_log_path": self.stage1_log_path,
            "stage2_path": self.stage2_path,
            "stage2_log_path": self.stage2_log_path,
            "stage3_sql_path": self.stage3_sql_path,
            "stage3_log_path": self.stage3_log_path,
            "stage3_validation_path": self.stage3_validation_path,
            "stage4_path": self.stage4_path,
            "log_path": self.log_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CohortRun":
        """Create from dict."""
        return cls(
            run_id=data["run_id"],
            name=data["name"],
            created_at=data["created_at"],
            status=RunStatus(data["status"]),
            user_inputs=UserInputs.from_dict(data["user_inputs"]),
            stages=[
                StageResult(
                    stage=s["stage"],
                    status=StageStatus(s["status"]),
                    started_at=s["started_at"],
                    completed_at=s.get("completed_at"),
                    metrics=StageMetrics(**s["metrics"]),
                    artifact_path=s.get("artifact_path"),
                )
                for s in data.get("stages", [])
            ],
            error=data.get("error", ""),
            total_duration_seconds=data.get("total_duration_seconds", 0.0),
            clarification_session=(
                ClarificationSession(**data["clarification_session"])
                if data.get("clarification_session")
                else None
            ),
            stage1_path=data.get("stage1_path"),
            stage1_log_path=data.get("stage1_log_path"),
            stage2_path=data.get("stage2_path"),
            stage2_log_path=data.get("stage2_log_path"),
            stage3_sql_path=data.get("stage3_sql_path"),
            stage3_log_path=data.get("stage3_log_path"),
            stage3_validation_path=data.get("stage3_validation_path"),
            stage4_path=data.get("stage4_path"),
            log_path=data.get("log_path"),
        )

    def get_display_name(self) -> str:
        """Get a display name for the run."""
        return f"{self.name} (#{self.run_id[:6]})"

    def get_current_stage(self) -> int:
        """Get the current stage number (1-4) or 0 if not started."""
        if not self.stages:
            return 0
        for stage in self.stages:
            if stage.status == StageStatus.RUNNING:
                return stage.stage
            if stage.status in (StageStatus.PENDING, StageStatus.FAILED):
                return stage.stage
        # All complete
        return 5

    def get_progress_percentage(self) -> float:
        """Get overall progress as percentage (0-100)."""
        if not self.stages:
            return 0.0
        completed = sum(1 for s in self.stages if s.status == StageStatus.COMPLETE)
        return (completed / len(self.stages)) * 100


@dataclass
class RunsIndex:
    """Index of all runs for quick listing."""

    runs: list[dict[str, Any]] = field(default_factory=list)

    def add_run(self, run: CohortRun) -> None:
        """Add a run to the index."""
        self.runs.append(
            {
                "run_id": run.run_id,
                "name": run.name,
                "created_at": run.created_at,
                "status": run.status.value,
            }
        )

    def remove_run(self, run_id: str) -> None:
        """Remove a run from the index."""
        self.runs = [r for r in self.runs if r["run_id"] != run_id]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {"runs": self.runs}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunsIndex":
        """Create from dict."""
        return cls(runs=data.get("runs", []))
