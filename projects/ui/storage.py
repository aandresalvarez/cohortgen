"""
File-based storage for run persistence.
"""

import json
from pathlib import Path
from typing import Optional

from projects.ui.models import CohortRun, RunsIndex


class RunStorage:
    """File-based storage for cohort runs."""

    def __init__(self, base_path: Path | str = "output/runs"):
        """Initialize storage with base directory."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_path / "runs_index.json"

    def _get_run_dir(self, run_id: str) -> Path:
        """Get the directory for a specific run."""
        return self.base_path / run_id

    def _ensure_run_dir(self, run_id: str) -> Path:
        """Ensure run directory exists."""
        run_dir = self._get_run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_run(self, run: CohortRun) -> None:
        """Save a run to disk."""
        run_dir = self._ensure_run_dir(run.run_id)
        run_file = run_dir / "run.json"

        with open(run_file, "w") as f:
            json.dump(run.to_dict(), f, indent=2)

        # Update index
        self._update_index_for_run(run)

    def load_run(self, run_id: str) -> Optional[CohortRun]:
        """Load a run from disk."""
        run_file = self._get_run_dir(run_id) / "run.json"
        if not run_file.exists():
            return None

        with open(run_file) as f:
            data = json.load(f)

        return CohortRun.from_dict(data)

    def delete_run(self, run_id: str) -> bool:
        """Delete a run from disk."""
        run_dir = self._get_run_dir(run_id)
        if not run_dir.exists():
            return False

        # Delete all files in the directory
        for file in run_dir.iterdir():
            if file.is_file():
                file.unlink()

        # Delete the directory
        run_dir.rmdir()

        # Update index
        index = self.load_index()
        index.remove_run(run_id)
        self.save_index(index)

        return True

    def list_runs(self) -> list[dict[str, str]]:
        """List all runs from the index."""
        index = self.load_index()
        # Sort by created_at descending
        return sorted(
            index.runs, key=lambda r: r.get("created_at", ""), reverse=True
        )

    def load_index(self) -> RunsIndex:
        """Load the runs index."""
        if not self.index_path.exists():
            return RunsIndex()

        with open(self.index_path) as f:
            data = json.load(f)

        return RunsIndex.from_dict(data)

    def save_index(self, index: RunsIndex) -> None:
        """Save the runs index."""
        with open(self.index_path, "w") as f:
            json.dump(index.to_dict(), f, indent=2)

    def _update_index_for_run(self, run: CohortRun) -> None:
        """Update the index with a run's current state."""
        index = self.load_index()

        # Remove existing entry if present
        index.remove_run(run.run_id)

        # Add updated entry
        index.add_run(run)

        # Save
        self.save_index(index)

    def save_artifact(
        self, run_id: str, filename: str, content: str | bytes
    ) -> str:
        """
        Save an artifact file for a run.

        Returns the absolute path to the saved file.
        """
        run_dir = self._ensure_run_dir(run_id)
        artifact_path = run_dir / filename

        if isinstance(content, str):
            with open(artifact_path, "w") as f:
                f.write(content)
        else:
            with open(artifact_path, "wb") as f:
                f.write(content)

        return str(artifact_path.absolute())

    def load_artifact(self, run_id: str, filename: str) -> Optional[str]:
        """Load an artifact file for a run."""
        artifact_path = self._get_run_dir(run_id) / filename
        if not artifact_path.exists():
            return None

        with open(artifact_path) as f:
            return f.read()

    def get_artifact_path(self, run_id: str, filename: str) -> str:
        """Get the absolute path for an artifact."""
        return str((self._get_run_dir(run_id) / filename).absolute())

