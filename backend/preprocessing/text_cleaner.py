import re


def clean_text(text: str) -> str:
    """
    Clean crime case text before NLP processing.
    """

    if not text:
        return ""

    # Remove unnecessary spaces
    text = re.sub(r"\s+", " ", text)

    # Remove unwanted special characters
    text = re.sub(r"[^\w\s.,!?'-]", "", text)

    # Remove leading/trailing spaces
    text = text.strip()

    return text