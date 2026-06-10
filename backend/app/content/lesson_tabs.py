import random


def lesson_tab_key(scene_set: str) -> str:
    return "delayed_lesson_tabs" if scene_set in {"delayed", "delayed_review"} else "lesson_tabs"


def lesson_tabs_from_session(session_config: dict, tab_key: str = "lesson_tabs") -> list[dict[str, str]]:
    return lesson_tabs_from_ordered_tabs(raw_lesson_tabs(session_config, tab_key))


def raw_lesson_tabs(session_config: dict, tab_key: str = "lesson_tabs") -> list[dict]:
    tabs = session_config.get(tab_key, [])
    if not isinstance(tabs, list):
        return []

    return [tab for tab in tabs if isinstance(tab, dict)]


def lesson_tabs_from_ordered_tabs(tabs: list[dict]) -> list[dict[str, str]]:
    lesson_tabs = []
    for tab in tabs:
        tab_id = tab.get("id")
        label = tab.get("label", tab_id)
        if tab_id and label:
            lesson_tabs.append({"id": str(tab_id), "label": str(label)})

    return lesson_tabs


def ordered_lesson_tabs(
    session_config: dict,
    tab_key: str,
    scene_set: str,
    order_seed: str | None = None,
) -> list[dict]:
    tabs = raw_lesson_tabs(session_config, tab_key)
    if tab_key == "delayed_lesson_tabs" or scene_set in {"delayed", "delayed_review"}:
        return shuffled_tabs(tabs, order_seed, "delayed")

    anchors = [tab for tab in tabs if not is_transfer_tab(tab)]
    transfers = [tab for tab in tabs if is_transfer_tab(tab)]
    return anchors + shuffled_tabs(transfers, order_seed, "transfer")


def shuffled_tabs(tabs: list[dict], order_seed: str | None, namespace: str) -> list[dict]:
    shuffled = list(tabs)
    if len(shuffled) < 2:
        return shuffled

    if order_seed is None:
        random.SystemRandom().shuffle(shuffled)
    else:
        random.Random(f"{namespace}:{order_seed}").shuffle(shuffled)
    return shuffled


def is_transfer_tab(tab: dict) -> bool:
    tab_id = str(tab.get("id", ""))
    card_id = str(tab.get("card_id", ""))
    return tab_id.endswith("-transfer") or "same_day_transfer" in card_id


def lessons_in_tab_order(lessons: list[dict], tabs: list[dict]) -> list[dict]:
    lessons_by_id = {str(item.get("id")): item for item in lessons if item.get("id")}
    ordered_lessons = []
    for tab in tabs:
        card_id = tab.get("card_id")
        if card_id and str(card_id) in lessons_by_id:
            ordered_lessons.append(lessons_by_id[str(card_id)])

    return ordered_lessons or lessons


def selected_lessons(lessons: list[dict], lesson: str, session_config: dict, tab_key: str = "lesson_tabs") -> list[dict]:
    lesson_aliases = lesson_aliases_from_session(session_config, tab_key)
    lesson_id = lesson_aliases.get(lesson, lesson)
    return [item for item in lessons if item.get("id") == lesson_id]


def lesson_aliases_from_session(session_config: dict, tab_key: str = "lesson_tabs") -> dict[str, str]:
    tabs = session_config.get(tab_key, [])
    if not isinstance(tabs, list):
        return {}

    aliases = {}
    for tab in tabs:
        if not isinstance(tab, dict):
            continue

        tab_id = tab.get("id")
        card_id = tab.get("card_id")
        if tab_id and card_id:
            aliases[str(tab_id)] = str(card_id)

    return aliases
