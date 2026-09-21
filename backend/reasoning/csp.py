"""
Constraint Satisfaction / Contradiction Detection
for AI Crime Investigator.

This module detects simple logical inconsistencies
in extracted case evidence and relationships.

Checks performed:
    1. Negative location statements.
    2. Negative ownership statements.
    3. Duplicate relationships.
    4. Opposite relationships between the same entities.
    5. Timeline contradictions (a person claims to have
       left at time T but evidence shows them present
       after time T).
"""

import re


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
# TIME PARSING (for timeline contradictions)
# ============================================================

_TIME_PATTERNS = [
    # 8:30 PM / 8:05 pm / 12:00 AM
    re.compile(
        r"^(\d{1,2}):(\d{2})\s*([ap]\.?m\.?)?$",
        re.IGNORECASE,
    ),
    # 8 PM / 8pm
    re.compile(
        r"^(\d{1,2})\s*([ap]\.?m\.?)$",
        re.IGNORECASE,
    ),
    # 20:30 (24-hour)
    re.compile(
        r"^(\d{1,2}):(\d{2})$",
    ),
]


def _parse_time_to_minutes(value):
    """
    Convert a time expression into minutes since midnight.

    Supported formats:
        - "8:30 PM"      -> 1230
        - "8:05 pm"
        - "8 PM"
        - "20:30"        -> 1230
        - "20:30:00"

    Returns:
        int | None:
            Minutes since midnight, or None if the
            expression cannot be parsed as a time.
    """
    text = _safe_string(value)

    if not text:
        return None

    text = text.split()[0] if text else ""

    if ":" not in text and not re.search(r"[ap]m", text):
        return None

    for pattern in _TIME_PATTERNS:

        match = pattern.match(text)

        if not match:
            continue

        groups = match.groups()

        if pattern is _TIME_PATTERNS[0]:
            hour = int(groups[0])
            minute = int(groups[1])
            ampm = groups[2] or ""
        elif pattern is _TIME_PATTERNS[1]:
            hour = int(groups[0])
            minute = 0
            ampm = groups[1] or ""
        else:
            hour = int(groups[0])
            minute = int(groups[1])
            ampm = ""

        if hour > 23 or minute > 59:
            return None

        if ampm:
            ampm = ampm.replace(".", "").lower()

            if ampm.startswith("a"):
                if hour == 12:
                    hour = 0
            elif ampm.startswith("p"):
                if hour != 12:
                    hour += 12

        return hour * 60 + minute

    return None


# Relation types that indicate a person was PRESENT at a time.
_PRESENCE_RELATION_TYPES = {
    "observed_at",
    "seen_at",
    "seen_near_at",
    "accessed_at",
    "reported_at",
    "at_time",
    "recorded_at",
}

# Relation types that indicate a person CLAIMED a departure time.
_CLAIM_RELATION_TYPES = {
    "claimed",
    "left_at",
    "departed_at",
    "stated_left_at",
}


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
    # 5. TIMELINE CONTRADICTIONS
    # --------------------------------------------------------
    #
    # If a person claims to have LEFT a location at a certain
    # time, but another piece of evidence places the SAME
    # person at the scene AFTER that claimed time, the two
    # statements conflict.

    #   claimed_departures: person -> {"time_text", "minutes"}
    #   presence_evidence:  person -> [(time_text, minutes, relation)]
    claimed_departures = {}
    presence_evidence = {}

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

        if not source or not target:
            continue

        # The person is the source of "claimed" edges;
        # presence can also appear with the person as source
        # (e.g. observed_at, accessed_at).

        # A claimed departure: person --claimed--> time.
        if relation_type in _CLAIM_RELATION_TYPES:

            minutes = _parse_time_to_minutes(target)

            if minutes is not None:
                claimed_departures.setdefault(
                    source, []
                ).append(
                    {
                        "time_text": target,
                        "minutes": minutes,
                    }
                )

        # Presence evidence: person --*_at--> time.
        if relation_type in _PRESENCE_RELATION_TYPES:

            minutes = _parse_time_to_minutes(target)

            if minutes is not None:
                presence_evidence.setdefault(
                    source, []
                ).append(
                    {
                        "time_text": target,
                        "minutes": minutes,
                        "relation": relation_type,
                    }
                )

    for person, departures in claimed_departures.items():

        for departure in departures:

            later_evidence = [
                evidence
                for evidence in presence_evidence.get(
                    person,
                    []
                )
                if evidence["minutes"] > (
                    departure["minutes"] + 1
                )
            ]

            for evidence in later_evidence:

                contradictions.append(
                    "Timeline contradiction: "
                    f"{person} claimed to have left at "
                    f"{departure['time_text'].upper()}, "
                    "but evidence places them at the scene "
                    f"at {evidence['time_text'].upper()}"
                    f" ({evidence['relation']})."
                )

    # --------------------------------------------------------
    # 6. RETURN UNIQUE RESULTS
    # --------------------------------------------------------

    return list(
        dict.fromkeys(
            contradictions
        )
    )