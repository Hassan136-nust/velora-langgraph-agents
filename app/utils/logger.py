"""
Structured logging for the multi-agent pipeline.
Stores log entries in-memory for UI display and also prints to console.
"""

import logging
from datetime import datetime, timezone
from typing import Optional


class AgentLogEntry:
    """Single log entry with agent metadata."""

    __slots__ = ("timestamp", "agent", "level", "message")

    def __init__(self, agent: str, level: str, message: str):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.agent = agent
        self.level = level
        self.message = message

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "agent": self.agent,
            "level": self.level,
            "message": self.message,
        }

    def __str__(self) -> str:
        icon = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "DEBUG": "🔍"}.get(
            self.level, "📝"
        )
        return f"[{self.level}] {icon} {self.agent} → {self.message}"


# Module-level store — shared across the pipeline run
_log_store: list[AgentLogEntry] = []


def clear_logs() -> None:
    """Reset the log store for a new pipeline run."""
    _log_store.clear()


def get_logs() -> list[dict]:
    """Return all log entries as dicts."""
    return [entry.to_dict() for entry in _log_store]


def get_log_lines() -> list[str]:
    """Return all log entries as formatted strings."""
    return [str(entry) for entry in _log_store]


def log(agent: str, level: str, message: str) -> None:
    """
    Add a log entry (stores in memory, doesn't print to console).

    Args:
        agent: Name of the agent (e.g. "Clarity Agent", "Research Agent").
        level: One of INFO, WARNING, ERROR, DEBUG.
        message: Human-readable message.
    """
    entry = AgentLogEntry(agent=agent, level=level, message=message)
    _log_store.append(entry)
    # Don't print to console - logs will be shown in the pipeline logs table at the end
