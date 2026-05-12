import re


TAMIL_INDEPENDENT_VOWELS = {
    "\u0b85": "a",
    "\u0b86": "aa",
    "\u0b87": "i",
    "\u0b88": "ii",
    "\u0b89": "u",
    "\u0b8a": "uu",
    "\u0b8e": "e",
    "\u0b8f": "ee",
    "\u0b90": "ai",
    "\u0b92": "o",
    "\u0b93": "oo",
    "\u0b94": "au",
}

TAMIL_CONSONANTS = {
    "\u0b95": "k",
    "\u0b99": "ng",
    "\u0b9a": "s",
    "\u0b9c": "j",
    "\u0b9e": "nj",
    "\u0b9f": "t",
    "\u0ba3": "n",
    "\u0ba4": "th",
    "\u0ba8": "n",
    "\u0ba9": "n",
    "\u0baa": "p",
    "\u0bae": "m",
    "\u0baf": "y",
    "\u0bb0": "r",
    "\u0bb1": "r",
    "\u0bb2": "l",
    "\u0bb3": "l",
    "\u0bb4": "zh",
    "\u0bb5": "v",
    "\u0bb7": "sh",
    "\u0bb8": "s",
    "\u0bb9": "h",
}

TAMIL_VOWEL_SIGNS = {
    "\u0bbe": "aa",
    "\u0bbf": "i",
    "\u0bc0": "ii",
    "\u0bc1": "u",
    "\u0bc2": "uu",
    "\u0bc6": "e",
    "\u0bc7": "ee",
    "\u0bc8": "ai",
    "\u0bca": "o",
    "\u0bcb": "oo",
    "\u0bcc": "au",
}

TAMIL_VIRAMA = "\u0bcd"
TAMIL_CHAR_PATTERN = re.compile(r"[\u0B80-\u0BFF]")


def phonetic_for_language(value: str, language: str) -> str:
    return romanize_for_language(value, language)


def romanize_for_language(value: str, language: str) -> str:
    if language == "ta" and contains_tamil(value):
        return tamil_to_latin(value)
    return value


def contains_tamil(value: str) -> bool:
    return bool(TAMIL_CHAR_PATTERN.search(value))


def tamil_to_latin(value: str) -> str:
    """Return a rough readable Tamil transliteration for learner feedback."""
    output: list[str] = []
    index = 0

    while index < len(value):
        char = value[index]

        if char in TAMIL_INDEPENDENT_VOWELS:
            output.append(TAMIL_INDEPENDENT_VOWELS[char])
            index += 1
            continue

        if char in TAMIL_CONSONANTS:
            base = TAMIL_CONSONANTS[char]
            next_char = value[index + 1] if index + 1 < len(value) else ""
            if next_char == TAMIL_VIRAMA:
                output.append(base)
                index += 2
            elif next_char in TAMIL_VOWEL_SIGNS:
                output.append(base + TAMIL_VOWEL_SIGNS[next_char])
                index += 2
            else:
                output.append(base + "a")
                index += 1
            continue

        if char in TAMIL_VOWEL_SIGNS or char == TAMIL_VIRAMA:
            index += 1
            continue

        output.append(char)
        index += 1

    return " ".join("".join(output).split())
