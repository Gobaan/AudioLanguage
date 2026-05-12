from difflib import SequenceMatcher


def normalize_for_match(value: str) -> str:
    value = value.casefold()
    normalized_chars = [
        char if (char.isalnum() or char.isspace()) else " "
        for char in value
    ]
    return " ".join("".join(normalized_chars).split())


def text_similarity(actual: str, expected: str) -> float:
    """Compare two text guesses with forgiving punctuation and case handling."""
    actual_normalized = normalize_for_match(actual)
    expected_normalized = normalize_for_match(expected)

    if not actual_normalized or not expected_normalized:
        return 0.0

    return SequenceMatcher(None, actual_normalized, expected_normalized).ratio()
