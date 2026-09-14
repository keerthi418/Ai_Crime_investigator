"""
Constraint Satisfaction / contradiction detection
for AI Crime Investigator.
"""


def detect_contradictions(text, relations):
    contradictions = []

    # Check direct positive/negative statements
    lower_text = text.lower()

    if "not near" in lower_text:
        contradictions.append(
            "A negative location relationship was detected."
        )

    if "not owned" in lower_text:
        contradictions.append(
            "A possible ownership contradiction was detected."
        )

    # Check duplicate source-target relationships
    seen = set()

    for relation in relations:
        key = (
            relation["source"].lower(),
            relation["target"].lower(),
            relation["relation"].lower()
        )

        if key in seen:
            contradictions.append(
                f"Duplicate relationship detected: "
                f"{relation['source']} -> {relation['target']}"
            )
        else:
            seen.add(key)

    return list(dict.fromkeys(contradictions))