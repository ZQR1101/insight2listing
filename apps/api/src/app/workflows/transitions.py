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


def advance_status(current: str, *targets: WorkflowState) -> str:
    """Apply forward-only targets in order and return the resulting status.

    Unknown current statuses fall back to DRAFT (the machine's entry point).
    Targets that would move backwards are skipped.
    """
    try:
        state = WorkflowState(current)
    except ValueError:
        state = WorkflowState.DRAFT
    for target in targets:
        if can_transition(state, target):
            state = target
    return state.value
