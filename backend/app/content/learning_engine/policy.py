TARGET_SESSION_SIZE = 3
HARD_SESSION_MAX = 5

REPAIR_PRIORITY = {
    "meaning_repair": 0,
    "recall_repair": 1,
    "transfer_repair": 2,
    "memory_repair": 3,
}


def is_anchor_stage(stage: str) -> bool:
    return stage == "guided_scene_production"


def is_transfer_stage(stage: str) -> bool:
    return stage == "same_day_transfer"


def is_delayed_stage(stage: str) -> bool:
    return stage == "delayed_review"
