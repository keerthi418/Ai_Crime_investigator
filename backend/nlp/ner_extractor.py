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
# EVIDENCE WORDS
# ============================================================

EVIDENCE_WORDS = {
    "cctv",
    "camera",
    "knife",
    "phone",
    "mobile",
    "fingerprint",
    "blood",
    "weapon",
    "vehicle",
    "car",
    "bike",
    "document",
    "photo",
    "photograph",
    "video",
    "laptop",
    "bag",
    "gun"
}


# ============================================================
# COMMON WORDS TO IGNORE
# ============================================================

IGNORED_WORDS = {
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
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
}


# ============================================================
# MAIN NER FUNCTION
# ============================================================

def extract_entities(text: str):
    """
    Extract important entities from a crime case description.

    Entity types:
        PERSON
        LOCATION
        DATE
        EVIDENCE
    """

    entities = []
    seen = set()

    # ========================================================
    # LOCATION EXTRACTION
    # ========================================================

    for location in KNOWN_LOCATIONS:

        pattern = r"\b" + re.escape(location) + r"\b"

        if re.search(pattern, text, re.IGNORECASE):

            key = (
                location.lower(),
                "LOCATION"
            )

            if key not in seen:

                entities.append({
                    "text": location,
                    "type": "LOCATION"
                })

                seen.add(key)

    # ========================================================
    # DATE EXTRACTION
    # ========================================================

    date_patterns = [

        # 12/08/2026
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        # 2026/08/12
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",

        # Monday, Tuesday, etc.
        r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b"
    ]

    for pattern in date_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for match in matches:

            key = (
                match.lower(),
                "DATE"
            )

            if key not in seen:

                entities.append({
                    "text": match,
                    "type": "DATE"
                })

                seen.add(key)

    # ========================================================
    # PERSON EXTRACTION
    # ========================================================

    # Example:
    # Ravi met Arun in Chennai
    #
    # Ravi  -> PERSON
    # Arun  -> PERSON
    # Chennai -> LOCATION

    person_pattern = r"\b[A-Z][a-zA-Z]{2,}\b"

    person_matches = re.findall(
        person_pattern,
        text
    )

    for person in person_matches:

        # Ignore common words
        if person in IGNORED_WORDS:
            continue

        # Ignore locations
        if any(
            person.lower() == location.lower()
            for location in KNOWN_LOCATIONS
        ):
            continue

        key = (
            person.lower(),
            "PERSON"
        )

        if key not in seen:

            entities.append({
                "text": person,
                "type": "PERSON"
            })

            seen.add(key)

    # ========================================================
    # EVIDENCE EXTRACTION
    # ========================================================

    for evidence in EVIDENCE_WORDS:

        pattern = r"\b" + re.escape(evidence) + r"\b"

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):

            key = (
                evidence.lower(),
                "EVIDENCE"
            )

            if key not in seen:

                entities.append({
                    "text": evidence,
                    "type": "EVIDENCE"
                })

                seen.add(key)

    # ========================================================
    # RETURN FINAL UNIQUE ENTITIES
    # ========================================================

    return entities