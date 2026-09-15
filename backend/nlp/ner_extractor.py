import re


# ============================================================
# KNOWN LOCATIONS
# ============================================================

KNOWN_LOCATIONS = {
    "Chennai",
    "Madurai",
    "Coimbatore",
    "Bangalore",
    "Bengaluru",
    "Mumbai",
    "Delhi",
    "Hyderabad",
    "Salem",
    "Trichy",
    "Tiruchirappalli",
    "Koyambedu",
    "Tambaram",
    "Vadapalani"
}


# ============================================================
# EVIDENCE TERMS
# ============================================================

EVIDENCE_TERMS = {
    "CCTV": "CCTV",
    "camera": "Camera",
    "phone": "Phone",
    "mobile phone": "Mobile Phone",
    "mobile": "Mobile",
    "fingerprint": "Fingerprint",
    "blood": "Blood Evidence",
    "weapon": "Weapon",
    "vehicle": "Vehicle",
    "car": "Car",
    "bike": "Bike",
    "document": "Document",
    "photo": "Photograph",
    "photograph": "Photograph",
    "video": "Video",
    "laptop": "Laptop",
    "bag": "Bag",
    "gun": "Gun",
    "message records": "Message Records",
    "phone records": "Phone Records",
    "bank records": "Bank Records",
    "transaction": "Bank Transaction",
    "bank account": "Bank Account",
    "IP address": "IP Address"
}


# ============================================================
# WORDS THAT SHOULD NOT BE PERSONS
# ============================================================

IGNORED_PERSON_WORDS = {
    "The",
    "This",
    "That",
    "These",
    "Those",
    "A",
    "An",
    "On",
    "At",
    "In",
    "Near",
    "From",
    "To",
    "And",
    "But",
    "With",
    "For",
    "By",
    "Of",
    "As",
    "However",
    "Therefore",
    "Then",
    "When",
    "Where",
    "Which",
    "Who",
    "What",
    "Why",
    "How",

    # Crime/evidence words
    "Unauthorized",
    "Transaction",
    "Bank",
    "Account",
    "CCTV",
    "Phone",
    "Mobile",
    "Records",
    "Message",
    "Messages",
    "Login",
    "Online",
    "Banking",
    "Portal",
    "Evidence",
    "Investigation",
    "Investigator",
    "Crime",
    "Case",
    "Report",
    "Records",
    "Contacted",
    "Communication",
    "Office",
    "Same",
    "Day",
    "Afternoon"
}


# ============================================================
# MONTHS
# ============================================================

MONTHS = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)


# ============================================================
# ADD ENTITY
# ============================================================

def add_entity(entities, seen, text, entity_type):
    """
    Add an entity only once.

    Example:
        Ravi Kumar -> PERSON
        CCTV -> EVIDENCE
    """

    text = text.strip()

    if not text:
        return

    key = (
        text.lower(),
        entity_type
    )

    if key in seen:
        return

    entities.append({
        "text": text,
        "type": entity_type
    })

    seen.add(key)


# ============================================================
# CHECK WHETHER TEXT IS A KNOWN LOCATION
# ============================================================

def is_location(text):
    """
    Check whether a given text is a known location.
    """

    return any(
        text.lower() == location.lower()
        for location in KNOWN_LOCATIONS
    )


# ============================================================
# MAIN NER FUNCTION
# ============================================================

def extract_entities(text: str):
    """
    Extract important entities from a crime investigation case.

    Supported entity types:

        PERSON
        LOCATION
        DATE
        EVIDENCE

    The extractor is designed for crime-investigation text
    such as:

        Ravi Kumar reported an unauthorized transaction.

        Arun Sharma received the money.

        CCTV showed Arun Sharma near Ravi Kumar.

        Priya contacted Arun Sharma.
    """

    entities = []
    seen = set()

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if not text:
        return entities

    if not isinstance(text, str):
        text = str(text)

    # ========================================================
    # 1. DATE EXTRACTION
    # ========================================================

    date_patterns = [

        # Example:
        # 15 September 2026
        rf"\b\d{{1,2}}\s+(?:{MONTHS})\s+\d{{4}}\b",

        # Example:
        # September 15, 2026
        rf"\b(?:{MONTHS})\s+\d{{1,2}},\s+\d{{4}}\b",

        # Example:
        # 15/09/2026
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        # Example:
        # 2026/09/15
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"
    ]

    for pattern in date_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for match in matches:

            add_entity(
                entities,
                seen,
                match,
                "DATE"
            )

    # ========================================================
    # 2. LOCATION EXTRACTION
    # ========================================================

    # Longer locations first.
    # Example:
    # Tiruchirappalli should be checked before shorter variants.

    for location in sorted(
        KNOWN_LOCATIONS,
        key=len,
        reverse=True
    ):

        pattern = (
            r"\b"
            + re.escape(location)
            + r"\b"
        )

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):

            add_entity(
                entities,
                seen,
                location,
                "LOCATION"
            )

    # ========================================================
    # 3. PERSON EXTRACTION
    # ========================================================
    #
    # Detect full names:
    #
    # Ravi Kumar
    # Arun Sharma
    #
    # Instead of:
    #
    # Ravi
    # Kumar
    # Arun
    # Sharma
    #
    # ========================================================

    full_name_pattern = (
        r"\b"
        r"[A-Z][a-z]{2,}"
        r"\s+"
        r"[A-Z][a-z]{2,}"
        r"\b"
    )

    full_names = re.findall(
        full_name_pattern,
        text
    )

    for name in full_names:

        words = name.split()

        # Ignore names containing unwanted words
        if any(
            word in IGNORED_PERSON_WORDS
            for word in words
        ):
            continue

        # Ignore locations
        if is_location(name):
            continue

        add_entity(
            entities,
            seen,
            name,
            "PERSON"
        )

    # ========================================================
    # 4. SINGLE-NAME PERSON EXTRACTION
    # ========================================================
    #
    # Some cases may contain:
    #
    # Priya contacted Arun Sharma.
    #
    # Here Priya is a valid person even though she has
    # no surname.
    #
    # ========================================================

    known_person_names = {
        "Ravi",
        "Arun",
        "Priya"
    }

    for person in known_person_names:

        pattern = (
            r"\b"
            + re.escape(person)
            + r"\b"
        )

        if not re.search(
            pattern,
            text,
            re.IGNORECASE
        ):
            continue

        # Check whether this person is already part
        # of a full name.

        already_full_name = any(
            entity["type"] == "PERSON"
            and person.lower()
            in entity["text"].lower().split()
            for entity in entities
        )

        if already_full_name:
            continue

        add_entity(
            entities,
            seen,
            person,
            "PERSON"
        )

    # ========================================================
    # 5. IP ADDRESS EXTRACTION
    # ========================================================

    ip_pattern = (
        r"\b"
        r"(?:\d{1,3}\.){3}\d{1,3}"
        r"\b"
    )

    ip_matches = re.findall(
        ip_pattern,
        text
    )

    for ip in ip_matches:

        add_entity(
            entities,
            seen,
            ip,
            "EVIDENCE"
        )

    # ========================================================
    # 6. MONEY EXTRACTION
    # ========================================================

    money_patterns = [

        # ₹85,000
        r"₹\s?\d+(?:,\d{3})*(?:\.\d+)?",

        # Rs. 85,000
        r"\bRs\.?\s?\d+(?:,\d{3})*(?:\.\d+)?",

        # 85000 rupees
        r"\b\d+(?:,\d{3})*\s+rupees\b"
    ]

    for pattern in money_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for amount in matches:

            add_entity(
                entities,
                seen,
                amount,
                "EVIDENCE"
            )

    # ========================================================
    # 7. TIME EXTRACTION
    # ========================================================

    time_patterns = [

        # 10:32 PM
        r"\b\d{1,2}:\d{2}\s?(?:AM|PM)\b",

        # 22:32
        r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b"
    ]

    for pattern in time_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for time_value in matches:

            add_entity(
                entities,
                seen,
                time_value,
                "EVIDENCE"
            )

    # ========================================================
    # 8. EVIDENCE EXTRACTION
    # ========================================================

    # Longest terms first.
    #
    # This ensures:
    #
    # Mobile Phone
    #
    # is detected before:
    #
    # Phone
    #

    sorted_evidence = sorted(
        EVIDENCE_TERMS.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for search_term, display_name in sorted_evidence:

        pattern = (
            r"\b"
            + re.escape(search_term)
            + r"\b"
        )

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):

            add_entity(
                entities,
                seen,
                display_name,
                "EVIDENCE"
            )

    # ========================================================
    # 9. ONLINE BANKING
    # ========================================================

    if re.search(
        r"\bonline banking\b",
        text,
        re.IGNORECASE
    ):

        add_entity(
            entities,
            seen,
            "Online Banking",
            "EVIDENCE"
        )

    # ========================================================
    # 10. LOGIN ACTIVITY
    # ========================================================

    if re.search(
        r"\blogin\b",
        text,
        re.IGNORECASE
    ):

        add_entity(
            entities,
            seen,
            "Login Activity",
            "EVIDENCE"
        )

    # ========================================================
    # 11. MESSAGE / COMMUNICATION EVIDENCE
    # ========================================================

    if re.search(
        r"\bmessage records?\b",
        text,
        re.IGNORECASE
    ):

        add_entity(
            entities,
            seen,
            "Message Records",
            "EVIDENCE"
        )

    if re.search(
        r"\bcommunication\b",
        text,
        re.IGNORECASE
    ):

        add_entity(
            entities,
            seen,
            "Communication Records",
            "EVIDENCE"
        )

    # ========================================================
    # 12. UNAUTHORIZED TRANSACTION
    # ========================================================

    if re.search(
        r"\bunauthorized transaction\b",
        text,
        re.IGNORECASE
    ):

        add_entity(
            entities,
            seen,
            "Unauthorized Transaction",
            "EVIDENCE"
        )

    # ========================================================
    # 13. CCTV FOOTAGE
    # ========================================================

    if re.search(
        r"\bCCTV footage\b",
        text,
        re.IGNORECASE
    ):

        add_entity(
            entities,
            seen,
            "CCTV Footage",
            "EVIDENCE"
        )

    # ========================================================
    # 14. FINAL CLEANUP
    # ========================================================

    # Remove accidental person entities that are actually
    # known evidence/location/date words.

    cleaned_entities = []

    for entity in entities:

        entity_text = entity["text"]

        if entity["type"] == "PERSON":

            if entity_text in IGNORED_PERSON_WORDS:
                continue

            if is_location(entity_text):
                continue

            # Don't allow obvious evidence words
            # to remain as PERSON.

            evidence_check = entity_text.lower()

            if evidence_check in {
                "cctv",
                "phone",
                "mobile",
                "camera",
                "transaction",
                "bank",
                "account",
                "records",
                "message",
                "login",
                "evidence"
            }:
                continue

        cleaned_entities.append(entity)

    # ========================================================
    # RETURN
    # ========================================================

    return cleaned_entities