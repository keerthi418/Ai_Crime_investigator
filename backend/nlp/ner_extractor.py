"""
Named Entity Recognition (NER)
-------------------------------

Extracts important entities from crime-investigation case text.

Supported entity types:
    PERSON
    LOCATION
    DATE
    EVIDENCE
    MONEY
    IP ADDRESS
    TIME

The extractor is rule-based and designed to provide
clean entities for the Relation Extraction and
Knowledge Graph modules.
"""

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
    "Vadapalani",
}


# ============================================================
# EVIDENCE TERMS
# ============================================================

EVIDENCE_TERMS = {
    "mobile phone": "Mobile Phone",
    "message records": "Message Records",
    "phone records": "Phone Records",
    "bank records": "Bank Records",
    "bank account": "Bank Account",
    "IP address": "IP Address",
    "fingerprint": "Fingerprint",
    "photograph": "Photograph",
    "transaction": "Bank Transaction",
    "unauthorized transaction": "Unauthorized Transaction",
    "CCTV footage": "CCTV Footage",
    "camera": "Camera",
    "phone": "Phone",
    "mobile": "Mobile",
    "CCTV": "CCTV",
    "blood": "Blood Evidence",
    "weapon": "Weapon",
    "vehicle": "Vehicle",
    "car": "Car",
    "bike": "Bike",
    "document": "Document",
    "photo": "Photograph",
    "video": "Video",
    "laptop": "Laptop",
    "bag": "Bag",
    "gun": "Gun",
}


# ============================================================
# WORDS THAT SHOULD NOT BE PERSONS
# ============================================================

IGNORED_PERSON_WORDS = {
    # Common words
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

    # Crime / investigation words
    "Unauthorized",
    "Transaction",
    "Bank",
    "Account",
    "CCTV",
    "Phone",
    "Mobile",
    "Records",
    "Record",
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
    "Contacted",
    "Communication",
    "Office",
    "Same",
    "Day",
    "Afternoon",

    # Evidence words
    "Camera",
    "Vehicle",
    "Car",
    "Bike",
    "Laptop",
    "Document",
    "Photo",
    "Photograph",
    "Video",
    "Weapon",
    "Gun",
    "Fingerprint",
    "Blood",
    "Bag",
}


# ============================================================
# KNOWN SINGLE-NAME PERSONS
# ============================================================

KNOWN_PERSON_NAMES = {
    "Ravi",
    "Arun",
    "Priya",
    "Kumar",
    "Rahul",
    "Vijay",
    "Ajay",
    "Anita",
    "Meena",
    "Suresh",
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

def add_entity(
    entities,
    seen,
    text,
    entity_type
):
    """
    Add an entity only once.

    Example:
        Ravi Kumar -> PERSON
        Chennai -> LOCATION
        CCTV -> EVIDENCE
    """

    if text is None:
        return

    text = str(text).strip()

    if not text:
        return

    key = (
        text.lower(),
        entity_type.upper()
    )

    if key in seen:
        return

    entities.append(
        {
            "text": text,
            "type": entity_type.upper()
        }
    )

    seen.add(key)


# ============================================================
# LOCATION CHECK
# ============================================================

def is_location(text):
    """
    Check whether text is a known location.
    """

    if not text:
        return False

    text_lower = text.strip().lower()

    return any(
        text_lower == location.lower()
        for location in KNOWN_LOCATIONS
    )


# ============================================================
# IP VALIDATION
# ============================================================

def is_valid_ip(ip):
    """
    Validate an IPv4 address.

    Example:
        192.168.1.10 -> True
        999.999.999.999 -> False
    """

    if not ip:
        return False

    parts = ip.split(".")

    if len(parts) != 4:
        return False

    try:
        return all(
            0 <= int(part) <= 255
            for part in parts
        )
    except ValueError:
        return False


# ============================================================
# MAIN NER FUNCTION
# ============================================================

def extract_entities(text: str):
    """
    Extract important entities from a crime-investigation case.

    Supported entity types:

        PERSON
        LOCATION
        DATE
        EVIDENCE
        MONEY
        IP ADDRESS
        TIME

    Example:

        Ravi Kumar reported an unauthorized transaction
        of ₹85,000. Arun Sharma accessed the account
        from IP address 192.168.1.10 in Chennai.
        CCTV showed Arun Sharma near Ravi Kumar.
    """

    entities = []
    seen = set()

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if text is None:
        return entities

    if not isinstance(text, str):
        text = str(text)

    text = text.strip()

    if not text:
        return entities

    # ========================================================
    # 1. DATE EXTRACTION
    # ========================================================

    date_patterns = [

        # 15 September 2026
        rf"\b\d{{1,2}}\s+(?:{MONTHS})\s+\d{{4}}\b",

        # September 15, 2026
        rf"\b(?:{MONTHS})\s+\d{{1,2}},\s+\d{{4}}\b",

        # 15/09/2026
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        # 2026/09/15
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
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
    # This prevents partial matching.

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

    # Detect two-word names.
    #
    # Examples:
    #   Ravi Kumar
    #   Arun Sharma
    #   Priya Devi

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

        # Ignore phrases containing unwanted words.
        if any(
            word in IGNORED_PERSON_WORDS
            for word in words
        ):
            continue

        # Ignore known locations.
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

    for person in KNOWN_PERSON_NAMES:

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

        # Check whether this person already belongs
        # to an extracted full name.

        already_full_name = any(
            entity["type"] == "PERSON"
            and person.lower()
            in entity["text"].lower().split()
            for entity in entities
        )

        if already_full_name:
            continue

        if person in IGNORED_PERSON_WORDS:
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
        r"(?:\d{1,3}\.){3}"
        r"\d{1,3}"
        r"\b"
    )

    ip_matches = re.findall(
        ip_pattern,
        text
    )

    for ip in ip_matches:

        if not is_valid_ip(ip):
            continue

        add_entity(
            entities,
            seen,
            ip,
            "IP ADDRESS"
        )

    # ========================================================
    # 6. MONEY EXTRACTION
    # ========================================================

    money_patterns = [

        # ₹85,000
        r"₹\s?\d+(?:,\d{3})*(?:\.\d+)?",

        # Rs. 85,000
        r"\bRs\.?\s?\d+(?:,\d{3})*(?:\.\d+)?",

        # INR 85,000
        r"\bINR\s?\d+(?:,\d{3})*(?:\.\d+)?",

        # $5,000
        r"\$\s?\d+(?:,\d{3})*(?:\.\d+)?",

        # €5,000
        r"€\s?\d+(?:,\d{3})*(?:\.\d+)?",

        # £5,000
        r"£\s?\d+(?:,\d{3})*(?:\.\d+)?",

        # 85000 rupees
        r"\b\d+(?:,\d{3})*\s+rupees\b",
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
                "MONEY"
            )

    # ========================================================
    # 7. TIME EXTRACTION
    # ========================================================

    time_patterns = [

        # 10:32 PM
        r"\b\d{1,2}:\d{2}\s?(?:AM|PM)\b",

        # 22:32
        r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b",
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
                "TIME"
            )

    # ========================================================
    # 8. EVIDENCE EXTRACTION
    # ========================================================

    # Longer terms first.
    #
    # Example:
    #
    # Mobile Phone
    #
    # should be detected before:
    #
    # Phone

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

            # Avoid adding generic "transaction"
            # when "unauthorized transaction" is already
            # represented.

            if (
                search_term == "transaction"
                and re.search(
                    r"\bunauthorized transaction\b",
                    text,
                    re.IGNORECASE
                )
            ):
                continue

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
        r"\b(?:login|logged in|login attempt|account access)\b",
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
    # 11. COMMUNICATION RECORDS
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
    # 14. EMAIL / PHISHING
    # ========================================================

    if re.search(
        r"\bphishing\b",
        text,
        re.IGNORECASE
    ):

        add_entity(
            entities,
            seen,
            "Phishing",
            "EVIDENCE"
        )

    if re.search(
        r"\bsuspicious email\b",
        text,
        re.IGNORECASE
    ):

        add_entity(
            entities,
            seen,
            "Suspicious Email",
            "EVIDENCE"
        )

    # ========================================================
    # 15. FINAL CLEANUP
    # ========================================================

    cleaned_entities = []

    for entity in entities:

        entity_text = entity["text"]
        entity_type = entity["type"]

        # -----------------------------------------------
        # PERSON cleanup
        # -----------------------------------------------

        if entity_type == "PERSON":

            if entity_text in IGNORED_PERSON_WORDS:
                continue

            if is_location(entity_text):
                continue

            lower_entity = entity_text.lower()

            obvious_non_persons = {
                "cctv",
                "phone",
                "mobile",
                "camera",
                "transaction",
                "bank",
                "account",
                "records",
                "record",
                "message",
                "messages",
                "login",
                "evidence",
                "vehicle",
                "car",
                "bike",
                "laptop",
                "document",
                "video",
                "weapon",
                "gun",
                "fingerprint",
                "blood",
            }

            if lower_entity in obvious_non_persons:
                continue

        # -----------------------------------------------
        # Keep valid entity
        # -----------------------------------------------

        cleaned_entities.append(entity)

    return cleaned_entities


# ============================================================
# BACKWARD-COMPATIBLE FUNCTION NAMES
# ============================================================

def extract_ner(text):
    """
    Backward-compatible alias for extract_entities().
    """

    return extract_entities(text)


def get_entities(text):
    """
    Backward-compatible alias for extract_entities().
    """

    return extract_entities(text)


def ner_extraction(text):
    """
    Backward-compatible alias for extract_entities().
    """

    return extract_entities(text)