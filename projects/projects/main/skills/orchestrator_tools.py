from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


def _projects_root() -> Path:
    # projects/main/skills/orchestrator_tools.py -> projects
    return Path(__file__).resolve().parents[2]


def _run_cli_in(dir_path: Path, *args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a CLI command in a given directory and return the CompletedProcess.

    Uses 'uv run flujo ...' if available on PATH; otherwise falls back to plain 'flujo'.
    """
    # Try uv run flujo; fallback to flujo
    cmd_uv = ["uv", "run", "flujo"] + list(args)
    try:
        return subprocess.run(
            cmd_uv, cwd=str(dir_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout
        )
    except Exception:
        cmd = ["flujo"] + list(args)
        return subprocess.run(
            cmd, cwd=str(dir_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout
        )


def _latest_debug_json(debug_dir: Path) -> Optional[Path]:
    if not debug_dir.exists():
        return None
    files = sorted(debug_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _parse_concept_sets_from_debug(debug_path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(debug_path.read_text())
    except Exception:
        return {"concept_sets": []}
    # Prefer summarized output if present
    steps = (data or {}).get("scratchpad", {}).get("steps") or {}
    summary = steps.get("summarize_concept_sets") or {}
    value = summary.get("value") if isinstance(summary, dict) else None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"concept_sets": []}
        except Exception:
            pass
    # Fallback: refined standard concepts output
    refine = steps.get("refine_to_standard_concepts") or {}
    if isinstance(refine, dict):
        try:
            parsed = refine
            return parsed if isinstance(parsed, dict) else {"concept_sets": []}
        except Exception:
            pass
    return {"concept_sets": []}


async def run_concept_discovery_subpipeline(cohort_definition: str) -> Dict[str, Any]:
    """Run the concept_discovery pipeline with the given cohort definition.

    Returns a dict suitable for updates_context merge: {"scratchpad": {"concept_sets": {...}}}
    """
    projects = _projects_root()
    proj_dir = projects / "concept_discovery"
    pipeline = proj_dir / "pipeline.yaml"
    debug_dir = proj_dir / "debug"

    args = ["run", "-p", str(pipeline), "--debug-export", "--input", cohort_definition]
    proc = _run_cli_in(proj_dir, *args, timeout=1200)
    # Parse latest debug JSON
    debug_file = _latest_debug_json(debug_dir)
    concept_sets = {"concept_sets": []}
    if debug_file:
        concept_sets = _parse_concept_sets_from_debug(debug_file)
    return {"scratchpad": {"concept_sets": concept_sets}}


def _parse_final_sql_from_debug(debug_path: Path) -> str:
    try:
        data = json.loads(debug_path.read_text())
    except Exception:
        return ""
    # Prefer scratchpad.final_sql if present
    scratch = (data or {}).get("scratchpad", {})
    sql = scratch.get("final_sql")
    if isinstance(sql, str) and sql.strip():
        return sql
    # Fallback to steps.final_sql.output.value
    steps = scratch.get("steps") or {}
    final = steps.get("final_sql") or {}
    if isinstance(final, dict):
        val = final.get("value") or final.get("output") or ""
        if isinstance(val, str):
            return val
    return ""


async def run_query_builder_subpipeline(payload: Dict[str, Any] | str) -> Dict[str, Any]:
    """Run the query_builder pipeline with JSON payload containing cohort_definition and concept_sets.

    Returns {"scratchpad": {"final_sql": str}}.
    """
    if isinstance(payload, dict):
        initial = json.dumps(payload)
    else:
        initial = str(payload or "")

    projects = _projects_root()
    proj_dir = projects / "query_builder"
    pipeline = proj_dir / "pipeline.yaml"
    debug_dir = proj_dir / "debug"

    args = ["run", "-p", str(pipeline), "--debug-export", "--input", initial]
    _ = _run_cli_in(proj_dir, *args, timeout=1800)
    debug_file = _latest_debug_json(debug_dir)
    sql = _parse_final_sql_from_debug(debug_file) if debug_file else ""
    return {"scratchpad": {"final_sql": sql}}
