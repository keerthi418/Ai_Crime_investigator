"""
Relation Extraction
-------------------

Creates clean entity-to-entity relationships
for the AI Crime Investigator.

Important rules:

    - A relationship target must always be an actual
      extracted entity, never an entire sentence.
    - Time / date values are only used as endpoints for
      meaningful edges (claimed, observed_at, recorded_at,
      accessed_at, involved_in).  They are never chained to
      each other in the generic fallback.
    - Every relation carries an explainable confidence and
      the evidence snippet that produced it, so the graph
      search and PDF report stay transparent.
"""

import re


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean(value):
    """
    Safely convert a value into a clean string.
    """
    if value is None:
        return ""

    return str(value).strip()


def _entity_text(entity):
    """
    Extract the text/name of an entity.

    Supported formats:

        {"text": "Ravi Kumar", "type": "PERSON"}

        {"label": "Ravi Kumar", "type": "PERSON"}

        {"name": "Ravi Kumar", "type": "PERSON"}

        "Ravi Kumar"
    """

    if isinstance(entity, dict):
        return _clean(
            entity.get("text")
            or entity.get("label")
            or entity.get("name")
        )

    return _clean(entity)


def _entity_type(entity):
    """
    Extract entity type safely.
    """

    if isinstance(entity, dict):
        return _clean(
            entity.get("type")
        ).upper()

    return ""


def _make_relation(source, relation, target, reason="",
                   confidence=0.8, relation_type="inferred"):
    """Create an explainable relationship."""
    return {
        "source": source,
        "relation": relation,
        "target": target,
        "reason": reason or (
            f"The relationship '{relation}' was detected "
            "from the case evidence."
        ),
        "confidence": round(float(confidence), 2),
        "relation_type": relation_type,
    }


# ============================================================
# ENTITY CATEGORISATION
# ============================================================

PERSON_TYPES = {"PERSON"}
LOCATION_TYPES = {"LOCATION", "GPE", "CITY", "PLACE"}
ORGANIZATION_TYPES = {"ORGANIZATION", "ORG", "COMPANY"}
EVIDENCE_TYPES = {"EVIDENCE", "ASSET", "IP", "IP ADDRESS", "MONEY"}
TIME_TYPES = {"TIME"}
DATE_TYPES = {"DATE"}

CORE_TYPES = (
    PERSON_TYPES
    | LOCATION_TYPES
    | ORGANIZATION_TYPES
    | EVIDENCE_TYPES
)

CARD_CODE_PATTERN = re.compile(r"^[A-Z]{2,6}-\d{2,6}$")
CCTV_NAME_PATTERN = re.compile(r"cctv|video|camera", re.IGNORECASE)


# ============================================================
# MAIN RELATION EXTRACTION
# ============================================================

def extract_relations(text, entities):
    """
    Extract simple and explainable relationships
    between entities found in the case description.

    Args:
        text (str):
            Original case description.

        entities (list):
            Entities extracted by the NER module.

    Returns:
        list:
            List of dictionaries containing:

            {
                "source": "...",
                "relation": "...",
                "target": "...",
                "reason": "...",
                "confidence": 0.85,
                "relation_type": "inferred"
            }
    """

    text = _clean(text)

    if not text or not entities:
        return []

    # --------------------------------------------------------
    # NORMALIZE ENTITIES
    # --------------------------------------------------------

    normalized_entities = []

    for entity in entities:

        entity_text = _entity_text(entity)

        if not entity_text:
            continue

        normalized_entities.append(
            {
                "text": entity_text,
                "type": _entity_type(entity)
            }
        )

    # Remove duplicate entities.
    unique_entities = []
    seen_entities = set()

    for entity in normalized_entities:

        key = entity["text"].lower()

        if key not in seen_entities:

            seen_entities.add(key)

            unique_entities.append(entity)

    normalized_entities = unique_entities

    if not normalized_entities:
        return []

    # --------------------------------------------------------
    # ENTITY MAPS
    # --------------------------------------------------------

    entity_lookup = {}

    for entity in normalized_entities:
        entity_lookup[entity["text"].lower()] = entity["text"]

    def canon(value):
        """Resolve a value to the canonical entity text."""
        if not value:
            return ""
        return entity_lookup.get(
            _clean(value).lower(),
            _clean(value)
        )

    people = [
        entity["text"]
        for entity in normalized_entities
        if entity["type"] in PERSON_TYPES
    ]

    locations = [
        entity["text"]
        for entity in normalized_entities
        if entity["type"] in LOCATION_TYPES
    ]

    organizations = [
        entity["text"]
        for entity in normalized_entities
        if entity["type"] in ORGANIZATION_TYPES
    ]

    evidence = [
        entity["text"]
        for entity in normalized_entities
        if entity["type"] in EVIDENCE_TYPES
        and not CARD_CODE_PATTERN.match(entity["text"])
    ]

    codes = [
        entity["text"]
        for entity in normalized_entities
        if CARD_CODE_PATTERN.match(entity["text"])
    ]

    cctv_devices = [
        entity["text"]
        for entity in normalized_entities
        if entity["type"] in EVIDENCE_TYPES
        and CCTV_NAME_PATTERN.search(entity["text"])
    ]

    times = [
        entity["text"]
        for entity in normalized_entities
        if entity["type"] in TIME_TYPES
    ]

    dates = [
        entity["text"]
        for entity in normalized_entities
        if entity["type"] in DATE_TYPES
    ]

    def entity_not_in(entities_list, value):
        value_lower = _clean(value).lower()
        return not any(
            _clean(item).lower() == value_lower
            for item in entities_list
        )

    # --------------------------------------------------------
    # RELATION STORAGE
    # --------------------------------------------------------

    relations = []
    relation_keys = set()

    def add(source, relation, target, reason="", confidence=0.85,
            node_types=None):
        """
        Add a relation only when both source and target
        are valid extracted entities.
        """

        source = canon(source)
        relation = _clean(relation)
        target = canon(target)

        if not source or not target or not relation:
            return

        # Only allow relation types that are not self relationships.
        if source.lower() == target.lower():
            return

        if node_types is None:
            node_types = CORE_TYPES

        # Verify both endpoints exist as real entities.
        if (
            source.lower() not in entity_lookup
            or target.lower() not in entity_lookup
        ):
            return

        relation_key = (
            source.lower(),
            relation.lower(),
            target.lower()
        )

        if relation_key in relation_keys:
            return

        relation_keys.add(relation_key)

        if not reason:

            for sentence in re.split(r"(?<=[.!?])\s+", text):
                low = sentence.lower()
                if (
                    source.lower() in low
                    and target.lower() in low
                ):
                    reason = sentence.strip()
                    break

            if not reason:
                reason = (
                    f"The case evidence indicates that "
                    f"{source} {relation} {target}."
                )

        relations.append(
            _make_relation(
                source,
                relation,
                target,
                reason,
                confidence=confidence,
            )
        )

    # --------------------------------------------------------
    # SENTENCE-LEVEL RULES
    # --------------------------------------------------------

    def near_phrases(matched):
        phrases = [
            "seen", "saw", "observed", "noticed", "spot",
            "came across", "near", "close to", "next to",
        ]
        return any(
            phrase in matched
            for phrase in phrases
        )

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence and sentence.strip()
    ]

    for sentence_index, sentence in enumerate(sentences):

        lower = sentence.lower()

        # Entities mentioned in this sentence.
        present = [
            entity["text"]
            for entity in normalized_entities
            if entity["text"].lower() in lower
        ]

        # Deduplicate while preserving order.
        present = list(dict.fromkeys(present))

        if not present:
            continue

        def present_of(entity_list):
            got = []
            for name in present:
                if name in entity_list:
                    got.append(name)
            return got

        present_people = present_of(people)
        present_locations = present_of(locations)
        present_orgs = present_of(organizations)
        present_evidence = present_of(evidence)
        present_codes = present_of(codes)
        present_cctv = present_of(cctv_devices)
        present_times = present_of(times)
        present_dates = present_of(dates)

        # ----------------------------------------------------
        # A. THEFT / MISSING
        # ----------------------------------------------------

        theft_phrases = (
            "stolen", "steal", "stole", "missing", "went missing",
            "lost", "robbed", "robbery", "theft", "took the",
            "nineteen", "broke in", "breaking in",
        )

        if any(
            phrase in lower
            for phrase in theft_phrases
        ):

            for evidence_item in present_evidence:

                # The reporting person -> the stolen item.
                for person in present_people:
                    add(
                        person,
                        "reported",
                        evidence_item,
                        reason=sentence,
                        confidence=0.9,
                    )

                # Stolen item -> location / organization it
                # disappeared from.
                for location in present_locations:
                    add(
                        evidence_item,
                        "stolen_from",
                        location,
                        reason=sentence,
                        confidence=0.9,
                    )

                for organization in present_orgs:
                    add(
                        evidence_item,
                        "stolen_from",
                        organization,
                        reason=sentence,
                        confidence=0.9,
                    )

                if present_dates:
                    add(
                        evidence_item,
                        "involved_in",
                        present_dates[0],
                        reason=sentence,
                        confidence=0.75,
                    )

                # The reported time of the incident.
                for person in present_people:
                    for time_value in present_times:
                        add(
                            person,
                            "reported_at",
                            time_value,
                            reason=sentence,
                            confidence=0.75,
                        )

                for time_value in present_times:
                    add(
                        evidence_item,
                        "at_time",
                        time_value,
                        reason=sentence,
                        confidence=0.75,
                    )

        # ----------------------------------------------------
        # B. CLAIMED / STATEMENTS
        # ----------------------------------------------------

        claim_phrases = (
            "claimed", "stated", "said", "admitted", "alleged",
            "claims", "told",
        )

        if any(
            phrase in lower
            for phrase in claim_phrases
        ):

            for person in present_people:

                for time_value in present_times:
                    add(
                        person,
                        "claimed",
                        time_value,
                        reason=sentence,
                        confidence=0.9,
                    )

                # A claimed departure/arrival is attached to the
                # location to keep the graph connected.
                if "left" in lower or "was at" in lower:
                    for location in present_locations:
                        add(
                            person,
                            "claimed",
                            location,
                            reason=sentence,
                            confidence=0.8,
                        )

        # ----------------------------------------------------
        # C. OBSERVED / SEEN
        # ----------------------------------------------------

        seen_terms = (
            "seen", "saw", "observed", "noticed", "spotted",
        )

        if any(
            term in lower
            for term in seen_terms
        ):

            # Person -> person co-presence.
            for index_a, person_a in enumerate(present_people):
                for person_b in present_people[index_a + 1:]:
                    add(
                        person_a,
                        "observed_with",
                        person_b,
                        reason=sentence,
                        confidence=0.85,
                    )

            # Person -> nearby location.
            if "near" in lower or "close to" in lower:
                for person in present_people:
                    for location in present_locations:
                        add(
                            person,
                            "seen_near",
                            location,
                            reason=sentence,
                            confidence=0.9,
                        )

            # Person -> time they were observed.
            for person in present_people:
                for time_value in present_times:
                    add(
                        person,
                        "observed_at",
                        time_value,
                        reason=sentence,
                        confidence=0.85,
                    )

        # ----------------------------------------------------
        # D. CCTV / CAMERA RECORDING
        # ----------------------------------------------------

        cctv_terms = (
            "cctv", "camera", "footage", "recorded", "captured",
            "surveillance",
        )

        if present_cctv and any(
            term in lower
            for term in cctv_terms
        ):

            # Prefer the most specific CCTV device name
            # (e.g. "CCTV Camera 03" over "CCTV").
            camera = (
                max(present_cctv, key=len)
                if present_cctv
                else None
            )

            if camera is None:
                camera = present_evidence[0] if present_evidence else None

            if camera:

                for person in present_people:
                    add(
                        camera,
                        "recorded",
                        person,
                        reason=sentence,
                        confidence=0.9,
                    )

                for time_value in present_times:
                    add(
                        camera,
                        "recorded_at",
                        time_value,
                        reason=sentence,
                        confidence=0.85,
                    )

                if present_locations:
                    add(
                        camera,
                        "located_at",
                        present_locations[0],
                        reason=sentence,
                        confidence=0.8,
                    )

        # ----------------------------------------------------
        # E. ACCESS CARD / ENTRY
        # ----------------------------------------------------

        card_terms = (
            "access card", "card", "badge", "swipe", "entered",
            "entry", "keycard", "used to enter", "unlocked",
        )

        if any(
            term in lower
            for term in card_terms
        ):

            card = None

            if present_codes:
                card = present_codes[0]

            elif present_evidence and "card" in lower:
                card = present_evidence[0]

            if card:

                for location in present_locations:
                    add(
                        card,
                        "used_to_access",
                        location,
                        reason=sentence,
                        confidence=0.9,
                    )

                for time_value in present_times:
                    add(
                        card,
                        "accessed_at",
                        time_value,
                        reason=sentence,
                        confidence=0.85,
                    )

                for organization in present_orgs:
                    add(
                        card,
                        "used_to_access",
                        organization,
                        reason=sentence,
                        confidence=0.8,
                    )

        # ----------------------------------------------------
        # F. DIRECT LOCATION PRESENCE
        # ----------------------------------------------------

        presence_phrases = (
            "entered", "inside", "was in", "was at", "is in",
            "located in", "left the", "at the", "in the",
        )

        if any(
            phrase in lower
            for phrase in presence_phrases
        ):

            for location in present_locations:

                for person in present_people:
                    add(
                        person,
                        "located_at",
                        location,
                        reason=sentence,
                        confidence=0.8,
                    )

                for evidence_item in present_evidence:
                    add(
                        evidence_item,
                        "located_at",
                        location,
                        reason=sentence,
                        confidence=0.8,
                    )

        # ----------------------------------------------------
        # G. EMPLOYMENT
        # ----------------------------------------------------

        employment_phrases = (
            "works at", "worked at", "employee", "employed at",
            "joined", "works for", "worked for", "associate of",
        )

        if any(
            phrase in lower
            for phrase in employment_phrases
        ):

            for organization in present_orgs:
                for person in present_people:
                    add(
                        person,
                        "works_at",
                        organization,
                        reason=sentence,
                        confidence=0.9,
                    )

        # ----------------------------------------------------
        # H. REPORTED / CONTACTED (extra)
        # ----------------------------------------------------

        reported_phrases = (
            "reported", "contacted", "informed", "filed",
            "learned", "discovered",
        )

        if any(
            phrase in lower
            for phrase in reported_phrases
        ):

            for person in present_people:
                for evidence_item in present_evidence:
                    add(
                        person,
                        "reported",
                        evidence_item,
                        reason=sentence,
                        confidence=0.85,
                    )

        # ----------------------------------------------------
        # I. SAFE CO-OCCURRENCE FALLBACK
        # ----------------------------------------------------
        #
        # Only used when no specialised rule fired and the
        # sentence contains at least two core (non-time/date)
        # entities.  Time and date nodes are intentionally
        # excluded as fallback endpoints so the graph does not
        # fill up with meaningless chains such as
        # "8:30 PM -> 8:30 -> Laptop".

        if (
            not any([
                theft_phrases and any(
                    phrase in lower
                    for phrase in theft_phrases
                ),
                claim_phrases and any(
                    phrase in lower
                    for phrase in claim_phrases
                ),
                seen_terms and any(
                    term in lower
                    for term in seen_terms
                ),
                cctv_terms and any(
                    term in lower
                    for term in cctv_terms
                ),
                card_terms and any(
                    term in lower
                    for term in card_terms
                ),
                presence_phrases and any(
                    phrase in lower
                    for phrase in presence_phrases
                ),
                employment_phrases and any(
                    phrase in lower
                    for phrase in employment_phrases
                ),
                reported_phrases and any(
                    phrase in lower
                    for phrase in reported_phrases
                ),
            ])
        ):

            core_present = [
                name
                for name in present
                if (
                    name in people
                    or name in locations
                    or name in organizations
                    or name in evidence
                )
            ]

            core_present = list(
                dict.fromkeys(core_present)
            )

            if len(core_present) >= 2:

                for index_a in range(len(core_present)):
                    for index_b in range(
                        index_a + 1,
                        len(core_present),
                    ):

                        add(
                            core_present[index_a],
                            "associated_with",
                            core_present[index_b],
                            reason=sentence,
                            confidence=0.6,
                        )

    # ========================================================
    # LINK ELAPSED DATE TO THE FRAME ENTITY
    # ========================================================
    #
    # When the report date only appears in the opening/closure
    # sentence, attach it once to the lead person so it has a
    # real connection to the rest of the graph.

    if dates and people and not any(
        relation["relation"] == "involved_in"
        and relation["target"] == dates[0]
        for relation in relations
    ):

        lead_person = people[0]

        for sentence in sentences:
            if (
                lead_person.lower() in sentence.lower()
                and dates[0].lower() in sentence.lower()
            ):
                add(
                    lead_person,
                    "involved_in",
                    dates[0],
                    reason=sentence.strip(),
                    confidence=0.75,
                )
                break

    # ========================================================
    # RETURN
    # ========================================================

    return relations


# ============================================================
# BACKWARD-COMPATIBLE FUNCTION NAMES
# ============================================================

def extract_relationships(text, entities):
    """
    Backward-compatible alias.
    """

    return extract_relations(
        text,
        entities
    )


def get_relations(text, entities):
    """
    Backward-compatible alias.
    """

    return extract_relations(
        text,
        entities
    )