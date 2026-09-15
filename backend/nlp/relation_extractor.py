import re


# ============================================================
# RELATION EXTRACTION
# ============================================================
#
# This module extracts meaningful relationships from a crime
# investigation case description.
#
# Example:
#
# Ravi Kumar reported an unauthorized transaction.
#
# Ravi Kumar -> reported -> Unauthorized Transaction
#
# The transaction was transferred to Arun Sharma.
#
# Unauthorized Transaction -> transferred_to -> Arun Sharma
#
# Ravi Kumar shared his mobile phone with Priya.
#
# Ravi Kumar -> shared_phone -> Priya
#
# Priya contacted Arun Sharma.
#
# Priya -> contacted -> Arun Sharma
#
# ============================================================


# ============================================================
# GENERIC RELATION PATTERNS
# ============================================================

RELATION_PATTERNS = [

    # --------------------------------------------------------
    # reported
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+reported\s+(?:an?\s+)?"
        r"(?:unauthorized\s+)?transaction\b",
        "reported"
    ),

    # --------------------------------------------------------
    # transferred_to
    # --------------------------------------------------------
    (
        r"\b(?:the\s+)?(?:₹[\d,]+|rs\.?\s?[\d,]+|"
        r"[\d,]+\s+rupees)?\s*"
        r"transaction\s+(?:was\s+)?transferred\s+to\s+"
        r"(?:an?\s+account\s+belonging\s+to\s+)?(.+?)"
        r"(?=[.!?]|$)",
        "transferred_to"
    ),

    # --------------------------------------------------------
    # account_belongs_to
    # --------------------------------------------------------
    (
        r"\ban?\s+account\s+belonging\s+to\s+(.+?)"
        r"(?=[.!?]|$)",
        "account_belongs_to"
    ),

    # --------------------------------------------------------
    # near
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+near\s+(.+?)"
        r"(?=[.!?]|$)",
        "near"
    ),

    # --------------------------------------------------------
    # shared_phone
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+shared\s+(?:his|her|their|the)?\s*"
        r"(?:mobile\s+phone|phone|mobile)\s+with\s+(.+?)"
        r"(?=[.!?]|$)",
        "shared_phone"
    ),

    # --------------------------------------------------------
    # contacted
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+contacted\s+(.+?)"
        r"(?=[.!?]|$)",
        "contacted"
    ),

    # --------------------------------------------------------
    # communication
    # --------------------------------------------------------
    (
        r"\bcommunication\s+between\s+(.+?)\s+and\s+(.+?)"
        r"(?=[.!?]|$)",
        "communicated_with"
    ),

    # --------------------------------------------------------
    # message communication
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+(?:had\s+)?communication\s+with\s+(.+?)"
        r"(?=[.!?]|$)",
        "communicated_with"
    ),

    # --------------------------------------------------------
    # met
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+met\s+(.+?)"
        r"(?=[.!?]|$)",
        "met"
    ),

    # --------------------------------------------------------
    # saw
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+saw\s+(?:the\s+)?(.+?)"
        r"(?=[.!?]|$)",
        "saw"
    ),

    # --------------------------------------------------------
    # used
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+used\s+(?:a\s+|an\s+|the\s+)?(.+?)"
        r"(?=[.!?]|$)",
        "used"
    ),

    # --------------------------------------------------------
    # owned
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+owned\s+(?:a\s+|an\s+|the\s+)?(.+?)"
        r"(?=[.!?]|$)",
        "owned"
    ),

    # --------------------------------------------------------
    # found
    # --------------------------------------------------------
    (
        r"\b(.+?)\s+found\s+(?:a\s+|an\s+|the\s+)?(.+?)"
        r"(?=[.!?]|$)",
        "found"
    ),
]


# ============================================================
# HELPER: CLEAN ENTITY TEXT
# ============================================================

def clean_entity(value):
    """
    Clean extracted entity text.
    """

    if not value:
        return ""

    value = value.strip()

    # Remove common leading words
    value = re.sub(
        r"^(?:the|a|an|his|her|their|my|your|"
        r"account|person|individual)\s+",
        "",
        value,
        flags=re.IGNORECASE
    )

    # Remove common trailing words
    value = re.sub(
        r"\s+(?:during|on|at|in|from|using|"
        r"regarding|about|before|after)\b.*$",
        "",
        value,
        flags=re.IGNORECASE
    )

    # Remove commas
    value = value.strip(" ,")

    return value.strip()


# ============================================================
# HELPER: EXTRACT PERSON NAMES
# ============================================================

def extract_person_names(text):
    """
    Extract likely person names from the case.

    Examples:
        Ravi Kumar
        Arun Sharma
        Priya
    """

    names = []

    # --------------------------------------------------------
    # Full names
    # --------------------------------------------------------

    full_name_pattern = (
        r"\b[A-Z][a-z]{2,}"
        r"\s+"
        r"[A-Z][a-z]{2,}\b"
    )

    for match in re.findall(
        full_name_pattern,
        text
    ):

        if match not in names:
            names.append(match)

    # --------------------------------------------------------
    # Known single names commonly used in the case
    # --------------------------------------------------------

    known_single_names = {
        "Ravi",
        "Arun",
        "Priya"
    }

    for name in known_single_names:

        if re.search(
            r"\b" + re.escape(name) + r"\b",
            text,
            re.IGNORECASE
        ):

            # Don't add Ravi separately when
            # Ravi Kumar already exists.

            already_full_name = any(
                name.lower()
                in full_name.lower().split()
                for full_name in names
            )

            if not already_full_name:
                names.append(name)

    return names


# ============================================================
# HELPER: FIND PERSON IN TEXT
# ============================================================

def resolve_person(value, person_names):
    """
    Convert a captured phrase into the most likely
    person name.
    """

    value = clean_entity(value)

    if not value:
        return None

    # Exact full-name match
    for name in person_names:

        if value.lower() == name.lower():
            return name

    # Search full names inside captured text
    for name in sorted(
        person_names,
        key=len,
        reverse=True
    ):

        if re.search(
            r"\b" + re.escape(name) + r"\b",
            value,
            re.IGNORECASE
        ):
            return name

    return value


# ============================================================
# HELPER: ADD RELATION
# ============================================================

def add_relation(
    relations,
    seen,
    source,
    target,
    relation
):
    """
    Add a unique relation.
    """

    source = clean_entity(source)
    target = clean_entity(target)

    if not source or not target:
        return

    # Avoid self relationship
    if source.lower() == target.lower():
        return

    key = (
        source.lower(),
        target.lower(),
        relation.lower()
    )

    if key in seen:
        return

    relations.append({
        "source": source,
        "target": target,
        "relation": relation
    })

    seen.add(key)


# ============================================================
# SPECIALIZED EXTRACTION
# ============================================================

def extract_specialized_relations(
    text,
    person_names,
    relations,
    seen
):
    """
    Extract domain-specific crime investigation relations.
    """

    # ========================================================
    # 1. REPORTING UNAUTHORIZED TRANSACTION
    # ========================================================

    pattern = (
        r"\b("
        + "|".join(
            re.escape(name)
            for name in sorted(
                person_names,
                key=len,
                reverse=True
            )
        )
        + r")\s+"
        r"reported\s+(?:an?\s+)?"
        r"(?:unauthorized\s+)?transaction\b"
    )

    if person_names:

        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE
        ):

            source = resolve_person(
                match.group(1),
                person_names
            )

            add_relation(
                relations,
                seen,
                source,
                "Unauthorized Transaction",
                "reported"
            )

    # ========================================================
    # 2. TRANSACTION TRANSFERRED TO PERSON
    # ========================================================

    transfer_patterns = [

        # transaction ... transferred to Arun Sharma
        r"\btransaction\b.*?"
        r"\btransferred\s+to\s+"
        r"(?:an?\s+account\s+belonging\s+to\s+)?"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)",

        # transferred to an account belonging to Arun Sharma
        r"\btransferred\s+to\s+"
        r"an?\s+account\s+belonging\s+to\s+"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
    ]

    for pattern in transfer_patterns:

        for match in re.finditer(
            pattern,
            text
        ):

            target = resolve_person(
                match.group(1),
                person_names
            )

            if target:

                add_relation(
                    relations,
                    seen,
                    "Unauthorized Transaction",
                    target,
                    "transferred_to"
                )

    # ========================================================
    # 3. CCTV SHOWED PERSON NEAR PERSON
    # ========================================================

    cctv_pattern = (
        r"\bCCTV\b.*?"
        r"\bshowed\s+"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
        r"\s+near\s+"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
    )

    for match in re.finditer(
        cctv_pattern,
        text
    ):

        source = resolve_person(
            match.group(1),
            person_names
        )

        target = resolve_person(
            match.group(2),
            person_names
        )

        if source and target:

            add_relation(
                relations,
                seen,
                source,
                target,
                "near"
            )

    # ========================================================
    # 4. SHARED MOBILE PHONE
    # ========================================================

    shared_phone_pattern = (
        r"\b("
        + "|".join(
            re.escape(name)
            for name in sorted(
                person_names,
                key=len,
                reverse=True
            )
        )
        + r")\s+"
        r"stated\s+that\s+"
        r"(?:he|she|they)\s+"
        r"had\s+shared\s+"
        r"(?:his|her|their)?\s*"
        r"(?:mobile\s+phone|phone|mobile)"
        r"\s+with\s+"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
    )

    if person_names:

        for match in re.finditer(
            shared_phone_pattern,
            text,
            re.IGNORECASE
        ):

            source = resolve_person(
                match.group(1),
                person_names
            )

            target = resolve_person(
                match.group(2),
                person_names
            )

            if source and target:

                add_relation(
                    relations,
                    seen,
                    source,
                    target,
                    "shared_phone"
                )

    # Also support:
    #
    # Ravi Kumar shared his mobile phone with Priya.

    direct_shared_pattern = (
        r"\b("
        + "|".join(
            re.escape(name)
            for name in sorted(
                person_names,
                key=len,
                reverse=True
            )
        )
        + r")\s+"
        r"shared\s+(?:his|her|their)?\s*"
        r"(?:mobile\s+phone|phone|mobile)"
        r"\s+with\s+"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
    )

    if person_names:

        for match in re.finditer(
            direct_shared_pattern,
            text,
            re.IGNORECASE
        ):

            source = resolve_person(
                match.group(1),
                person_names
            )

            target = resolve_person(
                match.group(2),
                person_names
            )

            if source and target:

                add_relation(
                    relations,
                    seen,
                    source,
                    target,
                    "shared_phone"
                )

    # ========================================================
    # 5. PHONE RECORDS -> CONTACTED
    # ========================================================

    contacted_pattern = (
        r"\bPhone\s+records?\s+showed\s+"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
        r"\s+contacted\s+"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
    )

    for match in re.finditer(
        contacted_pattern,
        text
    ):

        source = resolve_person(
            match.group(1),
            person_names
        )

        target = resolve_person(
            match.group(2),
            person_names
        )

        if source and target:

            add_relation(
                relations,
                seen,
                source,
                target,
                "contacted"
            )

    # ========================================================
    # 6. MESSAGE RECORDS -> COMMUNICATION
    # ========================================================

    message_pattern = (
        r"\bmessage\s+records?\s+showed\s+"
        r"(?:communication\s+between\s+)?"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
        r"\s+and\s+"
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)"
    )

    for match in re.finditer(
        message_pattern,
        text
    ):

        source = resolve_person(
            match.group(1),
            person_names
        )

        target = resolve_person(
            match.group(2),
            person_names
        )

        if source and target:

            add_relation(
                relations,
                seen,
                source,
                target,
                "communicated_with"
            )

    # ========================================================
    # 7. GENERIC CONTACTED RELATIONS
    # ========================================================

    if person_names:

        person_pattern = "|".join(
            re.escape(name)
            for name in sorted(
                person_names,
                key=len,
                reverse=True
            )
        )

        generic_contacted = (
            r"\b("
            + person_pattern
            + r")\s+contacted\s+("
            + person_pattern
            + r")\b"
        )

        for match in re.finditer(
            generic_contacted,
            text,
            re.IGNORECASE
        ):

            source = resolve_person(
                match.group(1),
                person_names
            )

            target = resolve_person(
                match.group(2),
                person_names
            )

            if source and target:

                add_relation(
                    relations,
                    seen,
                    source,
                    target,
                    "contacted"
                )


# ============================================================
# MAIN FUNCTION
# ============================================================

def extract_relations(text):
    """
    Extract relationships from a crime investigation case.

    Returns:

    [
        {
            "source": "Ravi Kumar",
            "target": "Unauthorized Transaction",
            "relation": "reported"
        },
        {
            "source": "Unauthorized Transaction",
            "target": "Arun Sharma",
            "relation": "transferred_to"
        }
    ]
    """

    relations = []
    seen = set()

    if not text:
        return relations

    if not isinstance(text, str):
        text = str(text)

    # ========================================================
    # 1. EXTRACT PERSON NAMES
    # ========================================================

    person_names = extract_person_names(text)

    # ========================================================
    # 2. SPECIALIZED CRIME RELATIONS
    # ========================================================

    extract_specialized_relations(
        text,
        person_names,
        relations,
        seen
    )

    # ========================================================
    # 3. GENERIC PATTERNS
    # ========================================================

    for pattern, relation_name in RELATION_PATTERNS:

        matches = re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:

            if len(match.groups()) < 2:
                continue

            source = clean_entity(
                match.group(1)
            )

            target = clean_entity(
                match.group(2)
            )

            # Try to resolve captured people
            if relation_name in {
                "met",
                "saw",
                "near",
                "contacted",
                "communicated_with",
                "shared_phone"
            }:

                source = resolve_person(
                    source,
                    person_names
                ) or source

                target = resolve_person(
                    target,
                    person_names
                ) or target

            add_relation(
                relations,
                seen,
                source,
                target,
                relation_name
            )

    # ========================================================
    # 4. REMOVE BAD GENERIC RELATIONS
    # ========================================================

    cleaned = []

    for relation in relations:

        source = relation["source"]
        target = relation["target"]

        # Don't allow obvious sentence words as entities
        bad_words = {
            "the",
            "this",
            "that",
            "however",
            "therefore",
            "bank",
            "account",
            "records",
            "phone",
            "mobile",
            "cctv",
            "transaction"
        }

        if source.lower() in bad_words:
            continue

        if target.lower() in bad_words:
            continue

        cleaned.append(relation)

    # ========================================================
    # 5. FINAL UNIQUE RELATIONS
    # ========================================================

    final_relations = []
    final_seen = set()

    for relation in cleaned:

        key = (
            relation["source"].lower(),
            relation["target"].lower(),
            relation["relation"].lower()
        )

        if key in final_seen:
            continue

        final_relations.append(
            relation
        )

        final_seen.add(key)

    return final_relations