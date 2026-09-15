import re


RELATION_PATTERNS = [
    (r"(\w+)\s+met\s+(\w+)", "met"),
    (r"(\w+)\s+saw\s+(?:the\s+)?(\w+)", "saw"),
    (r"(\w+)\s+owned\s+(?:a\s+|the\s+)?(\w+)", "owned"),
    (r"(\w+)\s+found\s+(?:a\s+|the\s+)?(\w+)", "found"),
    (r"(\w+)\s+used\s+(?:a\s+|the\s+)?(\w+)", "used"),
    (r"(\w+)\s+near\s+(\w+)", "near"),
]


def extract_relations(text):
    relations = []

    for sentence in re.split(r"[.!?]", text):

        for pattern, relation_name in RELATION_PATTERNS:

            matches = re.findall(
                pattern,
                sentence,
                flags=re.IGNORECASE
            )

            for source, target in matches:

                relations.append({
                    "source": source,
                    "target": target,
                    "relation": relation_name
                })

    # Remove duplicates
    unique = []
    seen = set()

    for relation in relations:

        key = (
            relation["source"].lower(),
            relation["target"].lower(),
            relation["relation"].lower()
        )

        if key not in seen:
            unique.append(relation)
            seen.add(key)

    return unique