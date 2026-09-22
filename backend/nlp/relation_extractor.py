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
      accessed_at, accessed_on, event_date).  They are never chained to
      each other in the generic fallback.
    - Every relation carries an explainable confidence and
      the evidence snippet that produced it, so the graph
      search and PDF report stay transparent.
"""

import re


# ============================================================
# CLAIM-DENIAL PATTERNS
# ============================================================

_NEGATIVE_PRESENCE_RE = re.compile(
    r"\b(?:"
    r"was\s+not\s+present\s+at"
    r"|were\s+not\s+present\s+at"
    r"|was\s+never\s+at"
    r"|wasn'?t\s+(?:at|present\s+at)"
    r"|did\s+not\s+(?:visit|enter|go\s+to)"
    r"|didn'?t\s+(?:visit|enter|go\s+to)"
    r"|not\s+present\s+at"
    r")\b",
    re.IGNORECASE,
)

_NEGATIVE_CONTACT_RE = re.compile(
    r"\b(?:"
    r"did\s+not\s+(?:contact|call|message|text|phone|speak\s+to)"
    r"|didn'?t\s+(?:contact|call|message|text|phone|speak\s+to)"
    r"|never\s+(?:contacted|called|messaged|texted)"
    r"|denied\s+(?:contacting|calling)"
    r"|did\s+not\s+make\s+any\s+(?:calls|contact)"
    r")\b",
    re.IGNORECASE,
)

# A time-interval such as "between 10:00 PM and 11:30 PM" or
# "entering at 10:15 PM and leaving at 11:20 PM".  The second
# time may be separated from "and" by a few connecting words.
_INTERVAL_RE = re.compile(
    r"\b(\d{1,2}:\d{2}\s?(?:a\.?m\.?|p\.?m\.?)?)\s+and\s+"
    r"(?:\w+\s+){0,4}?(\d{1,2}:\d{2}\s?(?:a\.?m\.?|p\.?m\.?)?)\b",
    re.IGNORECASE,
)


def _extract_interval(lower):
    """
    Extract (start, end) time tokens from a sentence interval,
    or (None, None) when no interval is expressed.

    The tokens keep the original spacing so they stay consistent
    with the extracted TIME entities ("10:15 PM", not "10:15PM").
    """
    match = _INTERVAL_RE.search(lower)

    if not match:
        return None, None

    return match.group(1).strip(" "), match.group(2).strip(" ")


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
# ENTITY PRESENCE IN A SENTENCE
# ============================================================
#
# A case narrative rarely repeats a person's full name every
# time.  "Rahul Kumar" appears once in the text and afterwards
# the story refers to the same person as "Rahul".  Because the
# graph node is the full name, the relation extractor must be
# able to resolve a first-name (or last-name) mention back to
# the full extracted PERSON entity.  Otherwise every sentence
# that uses the short form is treated as containing no known
# person and no relation is created, leaving the person as an
# isolated graph node.

def _name_word_in_sentence(text_lower, lower):
    """
    Check whether any single word of a person's name appears as
    a whole word (word boundary) in a sentence.

    Examples (lowercased):

        "rahul"        matches "rahul stated that he left ..."
        "kumar"        matches "... kumar's employee card ..."
        "sam"          does NOT match "... samsung device ..."
        "rahul"        does NOT match "... rahulkumar ..."
    """

    for word in text_lower.split():

        word = word.strip("'")

        if len(word) <= 1:
            continue

        if re.search(
            r"\b" + re.escape(word) + r"\b",
            lower
        ):
            return True

        # "Rahul Kumar's" -> the possessive form is preserved.
        if re.search(
            r"\b" + re.escape(word) + r"'(?:s|S)?\b",
            lower
        ):
            return True

    return False


def _entity_in_sentence(entity, lower):
    """
    Decide whether an extracted entity is mentioned in a sentence.

    Rules:

        1. The canonical entity text appears verbatim in the
           sentence (existing substring match).

        2. For multi-word PERSON entities, any single name word
           appearing as a whole word counts as a mention so texts
           that switch between "Rahul Kumar" and "Rahul" still
           connect the person to the evidence.

    All other entity types require the full canonical phrase.
    """

    entity_text = _entity_text(entity)

    if not entity_text:
        return False

    text_lower = entity_text.casefold()

    if text_lower in lower:
        return True

    if _entity_type(entity) in PERSON_TYPES:
        return _name_word_in_sentence(text_lower, lower)

    return False


def _name_in_lower(value, lower):
    """
    Return the earliest whole-word position of any name word of a
    PERSON entity in a lowercased sentence (or -1 if absent).

    This mirrors _name_word_in_sentence() but yields a position so
    rules that need sentence DIRECTION (sender before a verb,
    recipient after "to", driver after "driver is") can resolve the
    subject and object correctly.

        _name_in_lower("Arun Kumar", "arun transferred ...") == 0
        _name_in_lower("Ravi",       "arun ... to ravi")      == 17
        _name_in_lower("Ravi",       "no mention")            == -1
    """

    if not value or not lower:
        return -1

    positions = []

    for word in str(value).split():

        word = word.strip("'").casefold()

        if len(word) <= 1:
            continue

        match = re.search(
            r"\b" + re.escape(word) + r"\b",
            lower,
        )

        if match:
            positions.append(match.start())
            continue

        match = re.search(
            r"\b" + re.escape(word) + r"'(?:s|S)?\b",
            lower,
        )

        if match:
            positions.append(match.start())

    return min(positions) if positions else -1


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

    money = [
        entity["text"]
        for entity in normalized_entities
        if entity["type"] in {"MONEY"}
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

    def with_meta(relation_name, source_name, target_name, **metadata):
        """
        Attach structured metadata (start_time, end_time, call_count,
        claim_type, ...) to a specific relation that was just added.

        The contradiction engine reads this metadata to compare a
        claim against independent evidence instead of comparing
        bare relationship labels.
        """
        for relation in relations:
            if (
                relation.get("relation") == relation_name
                and relation.get("source") == source_name
                and relation.get("target") == target_name
            ):
                relation["metadata"] = dict(metadata)
                return relation

        return None

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

        # Entities mentioned in this sentence.  A person addressed
        # only by first name ("Rahul" instead of "Rahul Kumar")
        # still resolves to the full PERSON entity so the graph
        # stays connected to the extracted name.
        present = [
            entity["text"]
            for entity in normalized_entities
            if _entity_in_sentence(
                entity,
                lower,
            )
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
        present_money = present_of(money)

        # A statement such as "stated that he was not present at
        # the warehouse between 10:00 PM and 11:30 PM" is a CLAIM
        # of absence.  It must be represented semantically as
        #   Arun Kumar --claimed_not_present_at--> Warehouse
        # and must never become a positive "located_at" / "claimed"
        # edge.  Likewise, "stated that he did not contact Ravi" is
        # a negative contact claim.
        denies_presence = bool(
            present_people
            and present_locations
            and _NEGATIVE_PRESENCE_RE.search(lower)
        )

        denies_contact = bool(
            len(present_people) >= 2
            and _NEGATIVE_CONTACT_RE.search(lower)
        )

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

            # A bare reference to "the theft" (e.g. "two days
            # before the theft") is an EVENT reference, not a
            # reporting verb.  The person -> reported -> evidence
            # edge is therefore only produced when the sentence
            # literally states that someone reported something.
            reported_literal = "reported" in lower

            for evidence_item in present_evidence:

                # The reporting person -> the stolen item.
                if reported_literal:
                    for person in present_people:
                        add(
                            person,
                            "reported",
                            evidence_item,
                            reason=sentence,
                            confidence=0.9,
                        )

                # Stolen item -> location / organization it
                # disappeared from.  Requires an actual theft
                # verb so neutral phrases such as "before the
                # theft" never invent a stolen_from edge.
                if any(
                    phrase in lower
                    for phrase in (
                        "stolen", "steal", "stole", "went missing",
                        "robbed", "robbery", "took the",
                        "broke in", "breaking in",
                    )
                ):
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
                        "event_date",
                        present_dates[0],
                        reason=sentence,
                        confidence=0.75,
                    )

                # The reported time of the incident.
                if reported_literal:
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
        # A2. OWNERSHIP
        # ----------------------------------------------------
        #
        # "The laptop belonged to employee Priya Sharma."
        # creates:
        #
        #     Laptop --belonged_to--> Priya Sharma
        #
        # The victim of a theft is otherwise never connected to
        # the stolen evidence and is left as an isolated node.

        ownership_phrases = (
            "belonged to", "belongs to", "belonging to",
            "belonged", "owned by", "owned", "owner of",
        )

        if any(
            phrase in lower
            for phrase in ownership_phrases
        ):

            # Evidence -> owning organization (preferred).  When
            # an organization is stated ("belongs to FastMove
            # Logistics") the person in the sentence must NOT be
            # reported as the owner.
            if present_orgs:

                for evidence_item in present_evidence:
                    for organization in present_orgs:
                        add(
                            evidence_item,
                            "belonged_to",
                            organization,
                            reason=sentence,
                            confidence=0.9,
                        )

            # Evidence -> owning person (fallback when no
            # organization is mentioned).
            else:

                for evidence_item in present_evidence:
                    for person in present_people:
                        add(
                            evidence_item,
                            "belonged_to",
                            person,
                            reason=sentence,
                            confidence=0.9,
                        )

            # Person -> owner_of -> premise / organization.
            #
            # "A second person, Karthik, was identified as the
            # owner of a temporary storage location near the
            # warehouse." should produce ONLY:
            #
            #     Karthik --owner_of--> Temporary Storage Location
            #
            # The owned object is the premise that FOLLOWS the
            # "owner of" phrase, so it is resolved positionally.
            if present_people and "owner of" in lower:

                owner_index = lower.find("owner of")

                owner_candidates = []
                for owned in present_locations + present_orgs:
                    position = lower.find(owned.casefold())
                    if position != -1:
                        owner_candidates.append(
                            (position, owned)
                        )

                if owner_candidates:
                    # Nearest premise after "owner of"; fall back
                    # to the nearest overall match.
                    after_owner = [
                        (position, owned)
                        for position, owned in owner_candidates
                        if position >= owner_index
                    ]
                    chosen = min(
                        after_owner or owner_candidates
                    )[1]

                    for person in present_people:
                        add(
                            person,
                            "owner_of",
                            chosen,
                            reason=sentence,
                            confidence=0.9,
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

            # ----------------------------------------------------
            # B1. NEGATIVE PRESENCE CLAIM
            # ----------------------------------------------------
            #
            # "Arun Kumar stated that he was not present at the
            #  warehouse between 10:00 PM and 11:30 PM"
            #
            #     Arun Kumar --claimed_not_present_at--> Warehouse
            #         { claim_type: "negative_presence",
            #           start_time: "10:00 PM",
            #           end_time: "11:30 PM" }
            #
            # This sentence must NOT produce:
            #     Arun Kumar --claimed--> 10:00 PM
            #     Arun Kumar --located_at--> Warehouse
            if denies_presence:

                start_time, end_time = _extract_interval(lower)

                for person in present_people:
                    for location in present_locations:
                        add(
                            person,
                            "claimed_not_present_at",
                            location,
                            reason=sentence,
                            confidence=0.9,
                        )
                        with_meta(
                            "claimed_not_present_at",
                            person,
                            location,
                            claim_type="negative_presence",
                            start_time=start_time,
                            end_time=end_time,
                        )

            # ----------------------------------------------------
            # B2. NEGATIVE CONTACT CLAIM
            # ----------------------------------------------------
            #
            # "Arun Kumar stated that he did not contact Ravi"
            #
            #     Arun Kumar --claimed_no_contact--> Ravi
            elif denies_contact:

                # The declarer ("Arun Kumar") is the person who
                # appears BEFORE the negation phrase; the person
                # who was allegedly not contacted appears AFTER it.
                # Only the declarer claims; the direction never has
                # to be repeated in reverse.
                negative_match = _NEGATIVE_CONTACT_RE.search(
                    lower
                )

                denial_position = (
                    negative_match.start()
                    if negative_match
                    else -1
                )

                declarer = None
                other = None

                for person in present_people:
                    position = _name_in_lower(
                        person,
                        lower,
                    )
                    if position != -1:
                        if position < denial_position:
                            declarer = person
                        else:
                            other = person

                if declarer and other and other != declarer:
                    add(
                        declarer,
                        "claimed_no_contact",
                        other,
                        reason=sentence,
                        confidence=0.9,
                    )
                    with_meta(
                        "claimed_no_contact",
                        declarer,
                        other,
                        claim_type="negative_contact",
                    )

            # ----------------------------------------------------
            # B3. POSITIVE CLAIM (existing behaviour)
            # ----------------------------------------------------
            else:

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
        # C2. PERSON NEAR A LOCATION (without "seen" wording)
        # ----------------------------------------------------
        #
        # "CCTV Camera 03 recorded Rahul Kumar near the Server
        # Room" has no "seen / observed" wording, yet it still
        # connects Rahul Kumar to the Server Room.  A bare
        # "near / close to / next to" presence is therefore its
        # own rule so the graph stays connected and the
        # "seen_near" relation is produced regardless of the
        # camera phrasing being used.

        near_terms = (
            "near", "close to", "next to",
        )

        if any(
            term in lower
            for term in near_terms
        ):

            # A premise that is "near" another premise without any
            # person being observed.
            #
            # "... owner of a temporary storage location near the
            #  warehouse."            ->
            #     Temporary Storage Location --near--> Warehouse
            if len(present_locations) >= 2:

                near_index = min(
                    index
                    for term in near_terms
                    if (index := lower.find(term)) != -1
                )

                before_locations = [
                    location
                    for location in present_locations
                    if lower.find(location.casefold()) != -1
                    and lower.find(location.casefold()) < near_index
                ]

                after_locations = [
                    location
                    for location in present_locations
                    if lower.find(location.casefold()) != -1
                    and lower.find(location.casefold()) > near_index
                ]

                if before_locations and after_locations:
                    near_source = max(
                        before_locations,
                        key=lambda loc: lower.find(loc.casefold()),
                    )
                    near_target = min(
                        after_locations,
                        key=lambda loc: lower.find(loc.casefold()),
                    )
                    add(
                        near_source,
                        "near",
                        near_target,
                        reason=sentence,
                        confidence=0.85,
                    )

            # Person -> nearby premise.  Skipped when the person
            # is declared the OWNER of a premise in the same
            # sentence, because "... the owner of a temporary
            # storage location near the warehouse" describes the
            # premise as near the warehouse, not the owner.
            if (
                present_people
                and present_locations
                and "owner of" not in lower
            ):

                for person in present_people:
                    for location in present_locations:
                        add(
                            person,
                            "seen_near",
                            location,
                            reason=sentence,
                            confidence=0.85,
                        )

        # ----------------------------------------------------
        # C3. WITNESSED (person -> person)
        # ----------------------------------------------------
        #
        # "Arun Das witnessed Rahul Kumar near the Server Room"
        # creates the directional relation:
        #
        #     Arun Das --witnessed--> Rahul Kumar
        #
        # Only the witness reports the subject, so the relation
        # is produced from the words BEFORE "witnessed" toward
        # the words AFTER it (never the reverse).

        witness_terms = (
            "witnessed", "witnessing", "witnesses", "witness",
        )

        witness_position = next(
            (
                index
                for term in witness_terms
                if (index := lower.find(term)) != -1
            ),
            None,
        )

        if witness_position is not None:

            before_people = [
                person
                for person in present_people
                if person.casefold() in lower[:witness_position]
            ]

            after_people = [
                person
                for person in present_people
                if person.casefold() in lower[
                    witness_position:
                ]
            ]

            for subject in before_people:
                for witness_target in after_people:
                    add(
                        subject,
                        "witnessed",
                        witness_target,
                        reason=sentence,
                        confidence=0.9,
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

                presence_interval = _extract_interval(lower)

                for person in present_people:
                    add(
                        camera,
                        "recorded",
                        person,
                        reason=sentence,
                        confidence=0.9,
                    )

                    # CCTV evidence of PRESENCE over an interval.
                    # "CCTV footage shows Arun Kumar entering at
                    #  10:15 PM and leaving at 11:20 PM" becomes:
                    #
                    #   CCTV Footage --recorded_presence--> Arun Kumar
                    #       { start_time: "10:15 PM",
                    #         end_time: "11:20 PM",
                    #         location: "Warehouse" }
                    #
                    # The contradiction engine compares this
                    # independent evidence against a claim of
                    # absence.
                    if presence_interval[0]:
                        add(
                            camera,
                            "recorded_presence",
                            person,
                            reason=sentence,
                            confidence=0.9,
                        )
                        with_meta(
                            "recorded_presence",
                            camera,
                            person,
                            start_time=presence_interval[0],
                            end_time=presence_interval[1],
                            location=(
                                present_locations[0]
                                if present_locations
                                else None
                            ),
                            device=camera,
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

            # The person behind the entry.  "Rahul Kumar's
            # employee card was used to enter the room at 8:05 PM"
            # contains no extracted card node, but it still proves
            # Rahul Kumar accessed the room at 8:05 PM; connecting
            # the person keeps him in the evidence graph instead of
            # leaving him isolated.
            for person in present_people:

                for time_value in present_times:
                    add(
                        person,
                        "accessed_at",
                        time_value,
                        reason=sentence,
                        confidence=0.85,
                    )

                for location in present_locations:
                    add(
                        person,
                        "used_to_access",
                        location,
                        reason=sentence,
                        confidence=0.85,
                    )

        # ----------------------------------------------------
        # E2. EXPLICIT "ACCESSED" (person -> premise)
        # ----------------------------------------------------
        #
        # "warehouse employee Arun Kumar accessed the warehouse
        # at 10:30 PM" creates:
        #
        #     Arun Kumar --accessed--> Warehouse
        #     Arun Kumar --accessed_at--> 10:30 PM
        #
        # The "accessed" verb is distinct from the card rule (E)
        # because no card/badge device needs to be named.

        if "accessed" in lower:

            for person in present_people:
                for location in present_locations:
                    add(
                        person,
                        "accessed",
                        location,
                        reason=sentence,
                        confidence=0.9,
                    )

                for time_value in present_times:
                    add(
                        person,
                        "accessed_at",
                        time_value,
                        reason=sentence,
                        confidence=0.85,
                    )

        # ----------------------------------------------------
        # E3. DRIVER OF A VEHICLE
        # ----------------------------------------------------
        #
        # "The vehicle belongs to FastMove Logistics, whose
        # driver is Ravi." creates:
        #
        #     Ravi --driver_of--> Vehicle
        #
        # The driver is the person AFTER the "driver" phrase and
        # the vehicle is the evidence BEFORE it.

        driver_terms = (
            "driver is", "driver was", "driver of", "driven by",
            "driving the", "was driving",
        )

        driver_index = next(
            (
                index
                for term in driver_terms
                if (index := lower.find(term)) != -1
            ),
            None,
        )

        if driver_index is not None and present_people:

            vehicle = None
            for evidence_item in present_evidence:
                position = lower.find(evidence_item.casefold())
                if position != -1 and position < driver_index:
                    vehicle = evidence_item
                    break

            for person in present_people:
                position = _name_in_lower(person, lower)
                if position != -1 and position >= driver_index:
                    if vehicle:
                        add(
                            person,
                            "driver_of",
                            vehicle,
                            reason=sentence,
                            confidence=0.9,
                        )

        # ----------------------------------------------------
        # E4. MONEY TRANSFER
        # ----------------------------------------------------
        #
        # "Bank records show Arun transferred ₹75,000 to Ravi"
        # creates:
        #
        #     Arun Kumar --transferred--> ₹75,000
        #     Arun Kumar --transferred_to--> Ravi
        #
        # Position is used so the sender and the receiver follow
        # the sentence direction instead of inferred list order.

        transfer_terms = (
            "transferred", "transfer", "wired", "deposited",
            "credited", "paid", "sent",
        )

        transfer_index = next(
            (
                index
                for term in transfer_terms
                if (index := lower.find(term)) != -1
            ),
            None,
        )

        if transfer_index is not None and present_money:

            sender = None
            for person in present_people:
                position = _name_in_lower(person, lower)
                if position != -1 and position < transfer_index:
                    sender = person
                    break

            for amount in present_money:
                add(
                    sender or present_people[0],
                    "transferred",
                    amount,
                    reason=sentence,
                    confidence=0.9,
                )

            after = lower[transfer_index:]
            relative_to = after.find(" to ")

            if relative_to != -1:

                to_position = transfer_index + relative_to

                recipient = None
                for person in present_people:
                    position = _name_in_lower(person, lower)
                    if position != -1 and position > to_position:
                        recipient = person
                        break

                if sender and recipient and recipient != sender:
                    add(
                        sender,
                        "transferred_to",
                        recipient,
                        reason=sentence,
                        confidence=0.9,
                    )

        # ----------------------------------------------------
        # E5. CONTACT / CALLS (person -> person)
        # ----------------------------------------------------
        #
        # "Arun contacted Ravi 23 times" creates:
        #
        #     Arun Kumar --contacted--> Ravi
        #
        # This produces a deliberate person-to-person edge and does
        # NOT emit any generic "reported" evidence relationship.

        contact_terms = (
            "contacted", "called", "messaged", "phoned",
            "texted", "spoke to",
        )

        contact_index = next(
            (
                index
                for term in contact_terms
                if (index := lower.find(term)) != -1
            ),
            None,
        )

        if contact_index is not None and len(present_people) >= 2:

            before = [
                person
                for person in present_people
                if (
                    position := _name_in_lower(person, lower)
                ) != -1
                and position < contact_index
            ]

            after = [
                person
                for person in present_people
                if (
                    position := _name_in_lower(person, lower)
                ) != -1
                and position > contact_index
            ]

            # A records device named in the sentence (Phone Records,
            # Message Records, Communication Records, ...).
            recordings = [
                item
                for item in present_evidence
                if re.search(
                    r"record|phone|call|message|communication",
                    item,
                    re.IGNORECASE,
                )
            ]

            for subject in before:
                for recipient in after:
                    add(
                        subject,
                        "contacted",
                        recipient,
                        reason=sentence,
                        confidence=0.9,
                    )

                    # "Phone records show that Arun Kumar called
                    #  Ravi 8 times between 10:30 PM and 11:10 PM"
                    # becomes:
                    #
                    #   Phone Records --recorded_calls--> Ravi
                    #       { call_count: 8,
                    #         start_time: "10:30 PM",
                    #         end_time: "11:10 PM",
                    #         caller: "Arun Kumar" }
                    #
                    call_counter = re.search(
                        r"\b(\d{1,3})\s+times?\b",
                        lower,
                    )

                    if recordings and call_counter:

                        device = recordings[0]
                        start_time, end_time = (
                            _extract_interval(lower)
                        )

                        add(
                            device,
                            "recorded_calls",
                            recipient,
                            reason=sentence,
                            confidence=0.9,
                        )
                        with_meta(
                            "recorded_calls",
                            device,
                            recipient,
                            call_count=int(
                                call_counter.group(1)
                            ),
                            start_time=start_time,
                            end_time=end_time,
                            caller=subject,
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

                # A denial statement ("was not present at ...")
                # must never create a positive person presence
                # edge.  Evidence devices may still be linked.
                if not denies_presence:
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
            "reported", "informed", "filed a report",
            "officially reported",
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
                ownership_phrases and any(
                    phrase in lower
                    for phrase in ownership_phrases
                ),
                seen_terms and any(
                    term in lower
                    for term in seen_terms
                ),
                near_terms and any(
                    term in lower
                    for term in near_terms
                ),
                witness_terms and any(
                    term in lower
                    for term in witness_terms
                ),
                cctv_terms and any(
                    term in lower
                    for term in cctv_terms
                ),
                card_terms and any(
                    term in lower
                    for term in card_terms
                ),
                "accessed" in lower,
                driver_terms and any(
                    term in lower
                    for term in driver_terms
                ),
                transfer_terms and any(
                    term in lower
                    for term in transfer_terms
                ),
                contact_terms and any(
                    term in lower
                    for term in contact_terms
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
    #
    # The label reflects what the sentence actually says:
    #
    #     "On 12 September, Arun Kumar accessed the warehouse"
    #         -> accessed_on
    #
    #     "On 18 September 2026 ... the laptop ... Priya Sharma"
    #         -> event_date

    if dates and people and not any(
        relation["relation"] in ("event_date", "accessed_on")
        and relation["target"] == dates[0]
        for relation in relations
    ):

        lead_person = people[0]

        for sentence in sentences:
            if (
                lead_person.lower() in sentence.lower()
                and dates[0].lower() in sentence.lower()
            ):

                sentence_lower = sentence.lower()

                date_label = (
                    "accessed_on"
                    if any(
                        verb in sentence_lower
                        for verb in (
                            "accessed",
                            "entered",
                            "visited",
                            "opened",
                        )
                    )
                    else "event_date"
                )

                add(
                    lead_person,
                    date_label,
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