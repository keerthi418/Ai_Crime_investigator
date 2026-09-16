"""
Constraint Satisfaction / Contradiction Detection
for AI Crime Investigator.

This module detects simple logical inconsistencies
in extracted case evidence and relationships.
"""


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _safe_string(value):
    """
    Convert a value safely into a lowercase string.
    """
    if value is None:
        return ""

    return str(value).strip().lower()


def _get_relation_value(relation, key):
    """
    Safely get a relation field.

    Supports dictionary-based relations and prevents
    crashes when incomplete relation data is received.
    """
    if not isinstance(relation, dict):
        return ""

    return _safe_string(
        relation.get(key, "")
    )


# ============================================================
# CONTRADICTION DETECTION
# ============================================================

def detect_contradictions(
    text="",
    relations=None
):
    """
    Detect contradictions in the investigation evidence.

    Checks:
        1. Negative location statements.
        2. Negative ownership statements.
        3. Duplicate relationships.
        4. Opposite relationships between the same entities.

    Args:
        text (str):
            Original investigation text.

        relations (list):
            Extracted relationships.

    Returns:
        list:
            Unique contradiction messages.
    """

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    text = text or ""
    relations = relations or []

    contradictions = []

    lower_text = _safe_string(text)

    # --------------------------------------------------------
    # 1. NEGATIVE LOCATION STATEMENTS
    # --------------------------------------------------------

    location_negative_patterns = [
        "not near",
        "not at",
        "not in",
        "was not near",
        "wasn't near",
        "was not at",
        "wasn't at"
    ]

    for pattern in location_negative_patterns:

        if pattern in lower_text:

            contradictions.append(
                "A negative location relationship "
                "was detected."
            )

            break

    # --------------------------------------------------------
    # 2. NEGATIVE OWNERSHIP STATEMENTS
    # --------------------------------------------------------

    ownership_negative_patterns = [
        "not owned",
        "does not own",
        "doesn't own",
        "did not own",
        "didn't own",
        "not belonging to",
        "does not belong to"
    ]

    for pattern in ownership_negative_patterns:

        if pattern in lower_text:

            contradictions.append(
                "A possible ownership contradiction "
                "was detected."
            )

            break

    # --------------------------------------------------------
    # 3. CHECK DUPLICATE RELATIONSHIPS
    # --------------------------------------------------------

    seen = set()

    for relation in relations:

        source = _get_relation_value(
            relation,
            "source"
        )

        target = _get_relation_value(
            relation,
            "target"
        )

        relation_type = _get_relation_value(
            relation,
            "relation"
        )

        # Ignore incomplete relationships.
        if not source or not target:
            continue

        key = (
            source,
            target,
            relation_type
        )

        if key in seen:

            contradictions.append(
                "Duplicate relationship detected: "
                f"{source} -> {target}"
            )

        else:

            seen.add(key)

    # --------------------------------------------------------
    # 4. CHECK OPPOSITE RELATIONSHIPS
    # --------------------------------------------------------

    positive_negative_pairs = {
        "near": "not near",
        "located_near": "not near",
        "owns": "does not own",
        "owned_by": "not owned by",
        "connected_to": "not connected to",
        "present_at": "not present at",
        "visited": "did not visit"
    }

    relation_map = {}

    for relation in relations:

        source = _get_relation_value(
            relation,
            "source"
        )

        target = _get_relation_value(
            relation,
            "target"
        )

        relation_type = _get_relation_value(
            relation,
            "relation"
        )

        if not source or not target or not relation_type:
            continue

        key = (
            source,
            target
        )

        if key not in relation_map:
            relation_map[key] = set()

        relation_map[key].add(
            relation_type
        )

    for (source, target), relation_types in relation_map.items():

        for positive, negative in positive_negative_pairs.items():

            if (
                positive in relation_types
                and negative in relation_types
            ):

                contradictions.append(
                    "Conflicting relationships detected: "
                    f"{source} -> {target} "
                    f"({positive} / {negative})."
                )

    # --------------------------------------------------------
    # 5. RETURN UNIQUE RESULTS
    # --------------------------------------------------------

    return list(
        dict.fromkeys(
            contradictions
        )
    )