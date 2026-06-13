"""
Live progress tracking for research pipeline.
In-memory store — tracks current agent/step/tool using research_id.
"""

from typing import Dict, Optional
from datetime import datetime

# In-memory progress store
# { research_id: { agent, step, tool, logs, started_at } }
_progress: Dict[int, dict] = {}


def init_progress(research_id: int):
    """Initialize the tracking state at the start of the research pipeline."""
    _progress[research_id] = {
        "current_agent": "Starting...",
        "current_step":  "Initializing",
        "current_tool":  None,
        "status":        "running",
        "logs":          [],
        "started_at":    datetime.utcnow().isoformat(),
        "percent":       0,
    }


def update_progress(
    research_id: int,
    agent: str,
    step: str,
    tool: Optional[str] = None,
    percent: int = 0,
):
    """Update the active agent, pipeline step, and tool execution progress."""
    if research_id not in _progress:
        init_progress(research_id)

    _progress[research_id].update({
        "current_agent": agent,
        "current_step":  step,
        "current_tool":  tool,
        "percent":       percent,
    })

    # Log entry
    log = f"[{agent}] {step}"
    if tool:
        log += f" → Tool: {tool}"
    _progress[research_id]["logs"].append(log)
    print(log)


def complete_progress(research_id: int):
    """Update progress tracking to completed status upon successful report generation."""
    if research_id in _progress:
        _progress[research_id].update({
            "current_agent": "Reporter",
            "current_step":  "Report Generated ✅",
            "current_tool":  None,
            "status":        "completed",
            "percent":       100,
        })


def fail_progress(research_id: int, error: str):
    """Update tracking states when the pipeline encounters an execution error."""
    if research_id in _progress:
        _progress[research_id].update({
            "status":       "failed",
            "current_step": f"Failed: {error}",
            "percent":      0,
        })


def get_progress(research_id: int) -> Optional[dict]:
    """Retrieve the current progress details for a specific research execution."""
    return _progress.get(research_id)


def clear_progress(research_id: int):
    """Free up in-memory storage resources for the specified research ID."""
    _progress.pop(research_id, None)