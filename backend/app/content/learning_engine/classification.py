from __future__ import annotations

from app.content.learning_engine.models import RepairCategory, TargetState


def repair_category_for_state(state: TargetState | None) -> RepairCategory:
    if state is None:
        return "new"
    if state.has_wrong_choice or state.last_choice_correct is False:
        return "meaning_repair"
    if state.failed_delayed and (state.anchor_passed or state.transfer_passed or state.delayed_passed):
        return "memory_repair"
    if state.failed_transfer and state.anchor_passed:
        return "transfer_repair"
    if state.last_attempt_status == "failed":
        return "recall_repair"
    if state.anchor_passed or state.transfer_passed or state.delayed_passed:
        return "healthy"
    return "new"
