import re


def tokenize(text: str):
    """
    Convert cleaned text into individual tokens.
    """

    if not text:
        return []

    tokens = re.findall(r"\b[\w'-]+\b", text)

    return tokens