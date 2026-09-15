"""
Bayesian-style evidence confidence engine
for AI Crime Investigator.
"""


def calculate_confidence(entities, relations, contradictions):
    """
    Calculate an explainable confidence score using:
    - extracted entities
    - discovered relationships
    - contradictions
    """

    # Starting prior confidence
    prior = 0.50

    # Evidence contribution
    entity_score = min(len(entities) * 0.04, 0.20)
    relation_score = min(len(relations) * 0.06, 0.25)

    # Contradictions reduce confidence
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

    # Keep score between 0 and 1
    confidence = max(0.0, min(confidence, 1.0))

    return round(confidence, 2)


def explain_confidence(entities, relations, contradictions):
    """
    Generate human-readable explanation.
    """

    explanation = []

    if entities:
        explanation.append(
            f"{len(entities)} entities were extracted from the case."
        )

    if relations:
        explanation.append(
            f"{len(relations)} relationships support the investigation."
        )

    if contradictions:
        explanation.append(
            f"{len(contradictions)} contradiction(s) reduced confidence."
        )
    else:
        explanation.append(
            "No major contradictions were detected."
        )

    return explanation