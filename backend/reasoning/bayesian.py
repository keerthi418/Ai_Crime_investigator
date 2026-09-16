"""
Bayesian-style Evidence Confidence Engine
for AI Crime Investigator.

This module calculates an explainable confidence score
based on extracted entities, relationships and contradictions.
"""


# ============================================================
# CONFIDENCE CALCULATION
# ============================================================

def calculate_confidence(
    entities=None,
    relations=None,
    contradictions=None
):
    """
    Calculate an explainable confidence score.

    Factors:
        - Entities increase confidence.
        - Relationships increase confidence.
        - Contradictions decrease confidence.

    Returns:
        float:
            Confidence value between 0.0 and 1.0.
    """

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    entities = entities or []
    relations = relations or []
    contradictions = contradictions or []

    # --------------------------------------------------------
    # PRIOR CONFIDENCE
    # --------------------------------------------------------

    # Initial confidence before analyzing evidence.
    prior = 0.50

    # --------------------------------------------------------
    # ENTITY CONTRIBUTION
    # --------------------------------------------------------

    # Each entity contributes 4%.
    # Maximum entity contribution = 20%.
    entity_score = min(
        len(entities) * 0.04,
        0.20
    )

    # --------------------------------------------------------
    # RELATIONSHIP CONTRIBUTION
    # --------------------------------------------------------

    # Each relationship contributes 6%.
    # Maximum relationship contribution = 25%.
    relation_score = min(
        len(relations) * 0.06,
        0.25
    )

    # --------------------------------------------------------
    # CONTRADICTION PENALTY
    # --------------------------------------------------------

    # Each contradiction reduces confidence by 10%.
    # Maximum penalty = 30%.
    contradiction_penalty = min(
        len(contradictions) * 0.10,
        0.30
    )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    confidence = (
        prior
        + entity_score
        + relation_score
        - contradiction_penalty
    )

    # --------------------------------------------------------
    # CLAMP VALUE
    # --------------------------------------------------------

    # Make sure the value always stays between 0 and 1.
    confidence = max(
        0.0,
        min(confidence, 1.0)
    )

    # Round to two decimal places.
    return round(
        confidence,
        2
    )


# ============================================================
# CONFIDENCE EXPLANATION
# ============================================================

def explain_confidence(
    entities=None,
    relations=None,
    contradictions=None
):
    """
    Generate a human-readable explanation
    for the calculated confidence score.

    Returns:
        list[str]:
            Explanation statements.
    """

    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    entities = entities or []
    relations = relations or []
    contradictions = contradictions or []

    explanation = []

    # --------------------------------------------------------
    # ENTITY EXPLANATION
    # --------------------------------------------------------

    if entities:

        explanation.append(
            f"{len(entities)} entities were extracted "
            "from the case."
        )

    else:

        explanation.append(
            "No entities were extracted from the case."
        )

    # --------------------------------------------------------
    # RELATIONSHIP EXPLANATION
    # --------------------------------------------------------

    if relations:

        explanation.append(
            f"{len(relations)} relationships support "
            "the investigation."
        )

    else:

        explanation.append(
            "No significant relationships were identified."
        )

    # --------------------------------------------------------
    # CONTRADICTION EXPLANATION
    # --------------------------------------------------------

    if contradictions:

        explanation.append(
            f"{len(contradictions)} contradiction(s) "
            "reduced the confidence score."
        )

    else:

        explanation.append(
            "No major contradictions were detected."
        )

    # --------------------------------------------------------
    # SCORE BREAKDOWN
    # --------------------------------------------------------

    confidence = calculate_confidence(
        entities=entities,
        relations=relations,
        contradictions=contradictions
    )

    confidence_percentage = (
        confidence * 100
    )

    explanation.append(
        f"Overall evidence confidence: "
        f"{confidence_percentage:.0f}%."
    )

    return explanation


# ============================================================
# CONFIDENCE DETAILS
# ============================================================

def get_confidence_details(
    entities=None,
    relations=None,
    contradictions=None
):
    """
    Return a detailed confidence breakdown.

    Useful for:
        - Frontend dashboard
        - PDF reports
        - Debugging
        - Explainable AI output
    """

    entities = entities or []
    relations = relations or []
    contradictions = contradictions or []

    # Calculate individual components.

    prior = 0.50

    entity_score = min(
        len(entities) * 0.04,
        0.20
    )

    relation_score = min(
        len(relations) * 0.06,
        0.25
    )

    contradiction_penalty = min(
        len(contradictions) * 0.10,
        0.30
    )

    confidence = (
        prior
        + entity_score
        + relation_score
        - contradiction_penalty
    )

    confidence = max(
        0.0,
        min(confidence, 1.0)
    )

    return {
        "prior": round(prior, 2),
        "entity_score": round(entity_score, 2),
        "relation_score": round(relation_score, 2),
        "contradiction_penalty": round(
            contradiction_penalty,
            2
        ),
        "confidence": round(
            confidence,
            2
        ),
        "confidence_percentage": round(
            confidence * 100,
            1
        ),
        "entity_count": len(entities),
        "relation_count": len(relations),
        "contradiction_count": len(contradictions)
    }