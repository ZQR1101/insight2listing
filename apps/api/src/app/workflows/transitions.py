"""Workflow state-transition validation (plan section 7.1 / 7.3)."""

from __future__ import annotations

from app.core.enums import PROJECT_STATE_ORDER, WorkflowState


def index_of(state: WorkflowState) -> int:
    return PROJECT_STATE_ORDER.index(state)


def can_transition(current: WorkflowState, target: WorkflowState) -> bool:
    """Allow only forward moves in the project state machine."""
    try:
        return index_of(target) >= index_of(current)
    except ValueError:
        return False
