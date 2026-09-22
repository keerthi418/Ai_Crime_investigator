"""
Constraint Satisfaction / Contradiction Detection
for AI Crime Investigator.

This module detects logical inconsistencies in extracted
case evidence by comparing a person's CLAIMS against
INDEPENDENT EVIDENCE, never by comparing relationship
labels alone.

Supported contradiction classes:

    1. Presence contradiction
       A person claims they were NOT present at a location
       between two times, but independent CCTV footage records
       that exact person AT that location during an overlapping
       interval.
            claimed_not_present_at  <->  recorded_presence

    2. Communication contradiction
       A person claims they did NOT contact another person,
       but independent phone records show the same caller
       contacting that exact recipient.
            claimed_no_contact  <->  recorded_calls

    3. Duplicate relationships
    4. Opposite relationships between the same entities
    5. Timeline contradictions (claim of a time vs. presence
       evidence placed after that claimed time)

Every returned contradiction is a STRUCTURED object:

    {
        "type": "presence_contradiction",
        "subject": "Arun Kumar",
        "claim": "...",
        "evidence": "...",
        "severity": "HIGH",
        "message": "..."
    }

The SAME list is consumed by the dashboard, investigation page,
PDF report, AI explanation and audit logs.
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


def _get_text(value):
    """
    Convert a value safely into its original-case string.
    Used for DISPLAY while _safe_string() is used for matching.
    """
    if value is None:
        return ""

    return str(value).strip()


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


def _relation_meta(relation, key):
    """
    Read a structured metadata field from a relation.

    The relation extractor stores interval / quantity details
    (start_time, end_time, call_count, caller, claim_type, ...)
    under relation["metadata"] so the contradiction engine can
    compare CLAIMS against EVIDENCE with real values instead of
    bare relationship labels.
    """
    if not isinstance(relation, dict):
        return None

    metadata = relation.get("metadata")

    if not isinstance(metadata, dict):
        return None

    return metadata.get(key)


def _make_contradiction(
    contra_type,
    subject,
    claim,
    evidence,
    severity="MEDIUM",
    message=None,
):
    """
    Build one structured contradiction object.

    Consumed identically by all five outputs:
        dashboard, investigation page, PDF, explanation, audit.
    """
    if not message:
        message = f"{claim} However, {evidence}"

    return {
        "type": contra_type,
        "subject": subject or "",
        "claim": claim,
        "evidence": evidence,
        "severity": severity,
        "message": message,
    }


def _format_time(value):
    """
    Normalise a time token for display ("10:30 pm" -> "10:30 PM").
    """
    return str(value or "").strip().upper()


# ============================================================
# TIME PARSING (for interval overlap checks)
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

    The engine compares CLAIMS against independent EVIDENCE:

        claimed_not_present_at  +  recorded_presence
            -> presence_contradiction

        claimed_no_contact      +  recorded_calls
            -> communication_contradiction

    and keeps a few relation-consistency checks (duplicates,
    opposite pairs, timeline) as structured objects.

    Args:
        text (str):
            Original investigation text.

        relations (list):
            Extracted relationships (with optional metadata).

    Returns:
        list[dict]:
            Unique structured contradiction objects.
    """

    text = text or ""
    relations = relations or []

    contradictions = []

    # --------------------------------------------------------
    # A. EVIDENCE-BASED CONTRADICTIONS
    # --------------------------------------------------------
    #
    # Collect claims and independent evidence facts, then
    # compare real values (subject, location, time interval /
    # quantity), never bare relationship labels.

    negative_presence = []
    recorded_presence = []
    negative_contact = []
    recorded_calls = []

    for relation in relations:

        if not isinstance(relation, dict):
            continue

        relation_type = _safe_string(
            relation.get("relation")
        )

        source = _get_text(
            relation.get("source")
        )

        target = _get_text(
            relation.get("target")
        )

        if not relation_type or not source or not target:
            continue

        if relation_type == "claimed_not_present_at":

            negative_presence.append({
                "subject": source,
                "location": target,
                "start": _relation_meta(
                    relation,
                    "start_time",
                ),
                "end": _relation_meta(
                    relation,
                    "end_time",
                ),
            })

        elif relation_type == "recorded_presence":

            recorded_presence.append({
                "subject": target,
                "location": _relation_meta(
                    relation,
                    "location",
                ),
                "start": _relation_meta(
                    relation,
                    "start_time",
                ),
                "end": _relation_meta(
                    relation,
                    "end_time",
                ),
                "device": source,
            })

        elif relation_type == "claimed_no_contact":

            negative_contact.append({
                "subject": source,
                "other": target,
            })

        elif relation_type == "recorded_calls":

            recorded_calls.append({
                "device": source,
                "callee": target,
                "caller": _relation_meta(
                    relation,
                    "caller",
                ),
                "count": _relation_meta(
                    relation,
                    "call_count",
                ),
                "start": _relation_meta(
                    relation,
                    "start_time",
                ),
                "end": _relation_meta(
                    relation,
                    "end_time",
                ),
            })

    def _times_overlap(start_a, end_a, start_b, end_b):
        """
        True when two time intervals overlap.

        When either interval cannot be parsed, the recorded
        evidence of the same subject at the same place is still
        taken as conflicting with the claim rather than silently
        discarded.
        """
        a_start = _parse_time_to_minutes(start_a)
        a_end = _parse_time_to_minutes(end_a)
        b_start = _parse_time_to_minutes(start_b)
        b_end = _parse_time_to_minutes(end_b)

        if None in (a_start, a_end, b_start, b_end):
            return True

        return not (a_end < b_start or b_end < a_start)

    # --------------------------------------------------------
    # A1. PRESENCE CONTRADICTIONS
    # --------------------------------------------------------
    #
    #   Claim:   Arun Kumar was not present at Warehouse
    #            between 10:00 PM and 11:30 PM.
    #   Evidence: CCTV Footage records Arun Kumar at Warehouse
    #            from 10:15 PM to 11:20 PM.

    for claim in negative_presence:

        for evidence in recorded_presence:

            if (
                claim["subject"].casefold()
                != evidence["subject"].casefold()
            ):
                continue

            if (
                claim["location"].casefold()
                != _safe_string(
                    evidence["location"] or ""
                )
            ):
                continue

            if not _times_overlap(
                claim["start"],
                claim["end"],
                evidence["start"],
                evidence["end"],
            ):
                continue

            intervals_known = bool(
                claim["start"]
                and claim["end"]
                and evidence["start"]
                and evidence["end"]
            )

            severity = "HIGH" if intervals_known else "MEDIUM"

            claim_text = (
                f"{claim['subject']} stated that he was not "
                f"present at {claim['location']}"
            )

            if claim["start"] and claim["end"]:
                claim_text += (
                    f" between {_format_time(claim['start'])} "
                    f"and {_format_time(claim['end'])}"
                )

            evidence_text = (
                f"{evidence['device']} records "
                f"{evidence['subject']} at "
                f"{evidence['location']}"
            )

            if evidence["start"] and evidence["end"]:
                evidence_text += (
                    f" from {_format_time(evidence['start'])} "
                    f"to {_format_time(evidence['end'])}"
                )

            contradictions.append(
                _make_contradiction(
                    "presence_contradiction",
                    claim["subject"],
                    claim_text,
                    evidence_text,
                    severity=severity,
                )
            )

    # --------------------------------------------------------
    # A2. COMMUNICATION CONTRADICTIONS
    # --------------------------------------------------------
    #
    #   Claim:   Arun Kumar stated that he did not contact Ravi.
    #   Evidence: Phone Records show 8 calls between
    #            Arun Kumar and Ravi between 10:30 PM and
    #            11:10 PM.

    for claim in negative_contact:

        for record in recorded_calls:

            if (
                claim["subject"].casefold()
                != _safe_string(
                    record["caller"] or ""
                )
            ):
                continue

            if (
                claim["other"].casefold()
                != record["callee"].casefold()
            ):
                continue

            claim_text = (
                f"{claim['subject']} stated that he did not "
                f"contact {claim['other']}"
            )

            evidence_text = (
                f"{record['device']} show "
                f"{record['count']} calls between "
                f"{claim['subject']} and {claim['other']}"
            )

            if record["start"] and record["end"]:
                evidence_text += (
                    f" between {_format_time(record['start'])} "
                    f"and {_format_time(record['end'])}"
                )

            contradictions.append(
                _make_contradiction(
                    "communication_contradiction",
                    claim["subject"],
                    claim_text,
                    evidence_text,
                    severity="HIGH",
                )
            )

    # --------------------------------------------------------
    # B. CHECK DUPLICATE RELATIONSHIPS
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

        if not source or not target:
            continue

        key = (
            source,
            target,
            relation_type
        )

        if key in seen:

            contradictions.append(
                _make_contradiction(
                    "duplicate_relationship",
                    source,
                    f"{source} -> {target} "
                    f"({relation_type}) appears more than once.",
                    "The same relationship was extracted repeatedly.",
                    severity="LOW",
                )
            )

        else:

            seen.add(key)

    # --------------------------------------------------------
    # C. CHECK OPPOSITE RELATIONSHIPS
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
                    _make_contradiction(
                        "opposite_relationships",
                        source,
                        f"Conflicting relationships for "
                        f"{source} -> {target}.",
                        f"{source} and {target} are connected by "
                        f"both '{positive}' and '{negative}'.",
                        severity="MEDIUM",
                    )
                )

    # --------------------------------------------------------
    # D. TIMELINE CONTRADICTIONS
    # --------------------------------------------------------
    #
    # If a person claims to have LEFT a location at a certain
    # time, but another piece of evidence places the SAME
    # person at the scene AFTER that claimed time, the two
    # statements conflict.

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
                    _make_contradiction(
                        "timeline_contradiction",
                        person,
                        f"{person} claimed to have left at "
                        f"{_format_time(departure['time_text'])}.",
                        f"Evidence places {person} at the scene "
                        f"at {_format_time(evidence['time_text'])} "
                        f"({evidence['relation']}).",
                        severity="MEDIUM",
                    )
                )

    # --------------------------------------------------------
    # E. RETURN UNIQUE RESULTS
    # --------------------------------------------------------

    unique = {}

    for contradiction in contradictions:

        key = (
            contradiction.get("type", ""),
            _safe_string(contradiction.get("subject", "")),
            contradiction.get("claim", ""),
            contradiction.get("evidence", ""),
        )

        unique[key] = contradiction

    return list(unique.values())