"""
Relation Extraction
-------------------

Creates clean entity-to-entity relationships
for the AI Crime Investigator.

Important rule:
A relationship target must always be an actual
extracted entity, never an entire sentence.
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


def _make_relation(source, relation, target):
    """
    Create the standard relation structure.
    """

    return {
        "source": source,
        "relation": relation,
        "target": target
    }


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
                "target": "..."
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

    # --------------------------------------------------------
    # REMOVE DUPLICATE ENTITIES
    # --------------------------------------------------------

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
    # RELATION STORAGE
    # --------------------------------------------------------

    relations = []

    relation_keys = set()

    def add(source, relation, target):
        """
        Add a relation only when both source and target
        are valid extracted entities.
        """

        source = _clean(source)
        relation = _clean(relation)
        target = _clean(target)

        if not source or not target or not relation:
            return

        # Prevent self relationships.
        if source.lower() == target.lower():
            return

        relation_key = (
            source.lower(),
            relation.lower(),
            target.lower()
        )

        if relation_key in relation_keys:
            return

        relation_keys.add(relation_key)

        relations.append(
            _make_relation(
                source,
                relation,
                target
            )
        )

    # --------------------------------------------------------
    # ENTITY LOOKUP HELPERS
    # --------------------------------------------------------

    def find_entity(keyword):
        """
        Find an extracted entity containing the keyword.
        """

        keyword = _clean(keyword).lower()

        if not keyword:
            return None

        for entity in normalized_entities:

            if keyword in entity["text"].lower():

                return entity["text"]

        return None

    def find_entity_by_type(*types):
        """
        Return all entities matching the requested types.
        """

        wanted_types = {
            _clean(entity_type).upper()
            for entity_type in types
        }

        return [
            entity["text"]
            for entity in normalized_entities
            if entity["type"] in wanted_types
        ]

    def has_phrase(*phrases):
        """
        Check whether any phrase exists in the case text.
        """

        lower_text = text.lower()

        return any(
            _clean(phrase).lower() in lower_text
            for phrase in phrases
        )

    # ========================================================
    # ENTITY GROUPS
    # ========================================================

    people = find_entity_by_type(
        "PERSON"
    )

    locations = find_entity_by_type(
        "LOCATION",
        "GPE",
        "CITY",
        "PLACE"
    )

    evidence = find_entity_by_type(
        "EVIDENCE",
        "MONEY",
        "IP",
        "IP ADDRESS",
        "DATE",
        "TIME"
    )

    # ========================================================
    # PERSON / VICTIM
    # ========================================================

    victim = None

    if people:
        victim = people[0]

    # ========================================================
    # MONEY / TRANSACTION
    # ========================================================

    money = None

    # First try entity type.
    for entity in normalized_entities:

        if entity["type"] == "MONEY":

            money = entity["text"]

            break

    # Then try currency symbols.
    if not money:

        currency_pattern = re.compile(
            r"(?:₹|\$|€|£)\s*[\d,]+(?:\.\d+)?"
        )

        for entity in normalized_entities:

            if currency_pattern.search(
                entity["text"]
            ):

                money = entity["text"]

                break

    # ========================================================
    # TRANSACTION ENTITY
    # ========================================================

    transaction = None

    transaction_keywords = (
        "transaction",
        "payment",
        "transfer",
        "withdrawal",
        "deposit"
    )

    for entity in normalized_entities:

        lower_entity = entity["text"].lower()

        if any(
            keyword in lower_entity
            for keyword in transaction_keywords
        ):

            transaction = entity["text"]

            break

    # --------------------------------------------------------
    # Victim -> Transaction
    # --------------------------------------------------------

    if victim and transaction:

        add(
            victim,
            "reported",
            transaction
        )

    # --------------------------------------------------------
    # Transaction -> Money
    # --------------------------------------------------------

    if transaction and money:

        add(
            transaction,
            "amount",
            money
        )

    # ========================================================
    # IP ADDRESS
    # ========================================================

    ip_address = None

    ip_pattern = re.compile(
        r"^(?:\d{1,3}\.){3}\d{1,3}$"
    )

    for entity in normalized_entities:

        entity_type = entity["type"]

        entity_value = entity["text"]

        if (
            entity_type in {
                "IP",
                "IP ADDRESS"
            }
            or ip_pattern.fullmatch(entity_value)
        ):

            ip_address = entity_value

            break

    # ========================================================
    # LOGIN ACTIVITY
    # ========================================================

    login_activity = None

    login_keywords = (
        "login",
        "logged in",
        "login attempt",
        "login activity",
        "account access"
    )

    for entity in normalized_entities:

        lower_entity = entity["text"].lower()

        if any(
            keyword in lower_entity
            for keyword in login_keywords
        ):

            login_activity = entity["text"]

            break

    # --------------------------------------------------------
    # Login -> IP
    # --------------------------------------------------------

    if login_activity and ip_address:

        add(
            login_activity,
            "source_ip",
            ip_address
        )

    # --------------------------------------------------------
    # IP -> Victim
    # --------------------------------------------------------

    if (
        victim
        and ip_address
        and has_phrase(
            "accessed",
            "login",
            "logged in",
            "email account",
            "account was accessed",
            "account access"
        )
    ):

        add(
            ip_address,
            "accessed",
            victim
        )

    # ========================================================
    # SUSPICIOUS EMAIL / PHISHING
    # ========================================================

    suspicious_email = None

    suspicious_keywords = (
        "email",
        "phishing",
        "suspicious",
        "link",
        "message"
    )

    for entity in normalized_entities:

        lower_entity = entity["text"].lower()

        if any(
            keyword in lower_entity
            for keyword in suspicious_keywords
        ):

            suspicious_email = entity["text"]

            break

    # --------------------------------------------------------
    # Suspicious Email -> Victim
    # --------------------------------------------------------

    if victim and suspicious_email:

        add(
            suspicious_email,
            "targeted",
            victim
        )

    # ========================================================
    # LOCATION RELATIONSHIPS
    # ========================================================

    if locations:

        primary_location = locations[0]

        # IP -> Location
        if ip_address:

            add(
                ip_address,
                "associated_location",
                primary_location
            )

        # Login -> Location
        if login_activity:

            add(
                login_activity,
                "occurred_in",
                primary_location
            )

    # ========================================================
    # GENERIC EVIDENCE RELATIONSHIPS
    # ========================================================

    if victim:

        for item in evidence:

            lower_item = item.lower()

            # Do not duplicate already processed entities.
            if item == money:
                continue

            if item == ip_address:
                continue

            if item == login_activity:
                continue

            # Unauthorized evidence.
            if "unauthorized" in lower_item:

                add(
                    victim,
                    "affected_by",
                    item
                )

    # ========================================================
    # DIRECT PERSON -> LOCATION RELATION
    # ========================================================

    if victim and locations:

        if has_phrase(
            "was in",
            "was at",
            "located in",
            "located at",
            "present in",
            "present at",
            "visited",
            "near"
        ):

            add(
                victim,
                "located_at",
                locations[0]
            )

    # ========================================================
    # PERSON -> EVIDENCE
    # ========================================================

    if victim:

        for entity in normalized_entities:

            entity_value = entity["text"]
            entity_type = entity["type"]

            if entity_value == victim:
                continue

            if entity_value in locations:
                continue

            if entity_value == transaction:
                continue

            if entity_value == money:
                continue

            if entity_value == ip_address:
                continue

            if entity_value == login_activity:
                continue

            # Only create relationship when the text
            # contains a meaningful evidence keyword.
            if entity_type == "EVIDENCE":

                if has_phrase(
                    "found",
                    "recovered",
                    "evidence",
                    "linked",
                    "connected",
                    "associated"
                ):

                    add(
                        victim,
                        "linked_to",
                        entity_value
                    )

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