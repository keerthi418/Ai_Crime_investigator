"""
Bayesian-style Evidence Confidence Engine
for AI Crime Investigator.

This module calculates an explainable confidence score
based on extracted entities, relationships, graph
connectivity and contradictions.

Evidence Confidence Score
-------------------------

    score = prior
          + entity_score
          + relation_score
          + source_corroboration
          + connectivity_bonus
          + path_bonus
          - contradiction_penalty

Where:

    prior                 = 0.40      (measured base rate)
    entity_score          = min(0.06 * n_entities, 0.22)
    relation_score        = min(0.06 * n_relations, 0.24)
    source_corroboration  = 0.04 if relation endpoints form
                            several distinct source/target pairs
                            (independent corroborating links)
    connectivity_bonus    = 0.06 if the knowledge graph is fully
                            connected, else 0.02 when it has at
                            most two components, else 0.00
    path_bonus            = 0.04 when a valid path exists between
                            the investigated start and target nodes
                            (real BFS/DFS/A* graph connectivity),
                            else 0.00
    contradiction_penalty = min(0.12 * n_contradictions, 0.34)

The final value is clamped to the range [0.0, 1.0] and the
result is displayed to investigators as "Evidence Confidence
Score: NN%".

ONE value is computed here and returned to the API, the UI and
the PDF — never a second, separately recalculated score.
"""


# ============================================================
# EVIDENCE CONFIDENCE SCORE
# ============================================================

def calculate_confidence(
    entities=None,
    relations=None,
    contradictions=None,
    connected=False,
    components=1,
    path_exists=None,
    **kwargs
):
    """
    Calculate an explainable EvIdentityScore.

    Factors:
        - Entities increase confidence.
        - Relationships increase confidence.
        - Separately corroborating relationships increase more.
        - A connected graph increases confidence.
        - A real path between the investigated start and target
          increases confidence (actual BFS/DFS/A* connectivity).
        - Contradictions decrease confidence.

    Args:
        entities (list, optional):
            Extracted NER entities.

        relations (list, optional):
            Extracted relationships.

        contradictions (list, optional):
            Detected contradictions.

        connected (bool, optional):
            Whether the knowledge graph is fully connected.

        components (int, optional):
            Number of connected components in the graph.

        path_exists (bool, optional):
            Whether the requested start and target nodes are
            connected by a real path in the knowledge graph.

    Returns:
        float:
            Evidence confidence score between 0.0 and 1.0.
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

    prior = 0.40

    # --------------------------------------------------------
    # ENTITY CONTRIBUTION
    # --------------------------------------------------------

    entity_score = min(
        len(entities) * 0.06,
        0.22
    )

    # --------------------------------------------------------
    # RELATIONSHIP CONTRIBUTION
    # --------------------------------------------------------

    relation_score = min(
        len(relations) * 0.06,
        0.24
    )

    # --------------------------------------------------------
    # SOURCE CORROBORATION
    # --------------------------------------------------------
    #
    # Relationships that connect many different source/target
    # pairs count as independent corroborating links rather
    # than one repeated statement.

    distinct_pairs = set()

    for relation in relations:

        if not isinstance(relation, dict):
            continue

        source = str(
            relation.get("source") or ""
        ).strip()

        target = str(
            relation.get("target") or ""
        ).strip()

        if source and target:
            distinct_pairs.add(
                (source.casefold(), target.casefold())
            )

    source_corroboration = (
        0.04
        if len(distinct_pairs) >= 3
        else 0.00
    )

    # --------------------------------------------------------
    # CONNECTIVITY BONUS
    # --------------------------------------------------------

    try:
        components = int(components or 1)
    except (TypeError, ValueError):
        components = 1

    if connected:
        connectivity_bonus = 0.06
    elif components <= 2:
        connectivity_bonus = 0.02
    else:
        connectivity_bonus = 0.00

    # --------------------------------------------------------
    # START -> TARGET PATH BONUS (real graph search)
    # --------------------------------------------------------

    path_bonus = 0.04 if path_exists else 0.00

    # --------------------------------------------------------
    # CONTRADICTION PENALTY
    # --------------------------------------------------------

    contradiction_penalty = min(
        len(contradictions) * 0.12,
        0.34
    )

    # --------------------------------------------------------
    # FINAL EVIDENCE CONFIDENCE SCORE
    # --------------------------------------------------------

    score = (
        prior
        + entity_score
        + relation_score
        + source_corroboration
        + connectivity_bonus
        + path_bonus
        - contradiction_penalty
    )

    score = max(0.0, min(score, 1.0))

    return round(score, 2)


# ============================================================
# CONFIDENCE EXPLANATION
# ============================================================

def explain_confidence(
    entities=None,
    relations=None,
    contradictions=None,
    connected=False,
    components=1,
    path_exists=None,
    start=None,
    target=None,
    **kwargs
):
    """
    Generate a human-readable explanation
    for the calculated Evidence Confidence Score.

    Returns:
        list[str]:
            Explanation statements.
    """

    entities = entities or []
    relations = relations or []
    contradictions = contradictions or []

    explanation = []

    score = calculate_confidence(
        entities=entities,
        relations=relations,
        contradictions=contradictions,
        connected=connected,
        components=components,
        path_exists=path_exists,
    )

    explanation.append(
        f"Evidence Confidence Score: {score * 100:.0f}%."
    )

    if entities:
        explanation.append(
            f"{len(entities)} entities were extracted "
            "from the case."
        )
    else:
        explanation.append(
            "No entities were extracted from the case."
        )

    if relations:
        explanation.append(
            f"{len(relations)} relationships support "
            "the investigation."
        )
    else:
        explanation.append(
            "No significant relationships were identified."
        )

    if contradictions:
        explanation.append(
            f"{len(contradictions)} contradiction(s) "
            "reduced the confidence score."
        )
    else:
        explanation.append(
            "No major contradictions were detected."
        )

    if connected:
        explanation.append(
            "The knowledge graph is fully connected, "
            "which supports the investigation."
        )
    else:
        try:
            components = int(components or 1)
        except (TypeError, ValueError):
            components = 1

        explanation.append(
            f"The knowledge graph contains {components} "
            "connected component(s), reducing confidence."
        )

    if path_exists:
        pair = (
            f"'{start}' and '{target}'"
            if start and target
            else "the selected start and target"
        )
        explanation.append(
            f"A valid path exists between {pair}, "
            "which supports the investigation."
        )
    elif path_exists is False and start and target:
        explanation.append(
            f"No path exists between '{start}' and '{target}' "
            "in the knowledge graph."
        )

    return explanation


# ============================================================
# CONFIDENCE DETAILS
# ============================================================

def get_confidence_details(
    entities=None,
    relations=None,
    contradictions=None,
    connected=False,
    components=1,
    path_exists=None,
    **kwargs
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

    prior = 0.40

    entity_score = min(
        len(entities) * 0.06,
        0.22
    )

    relation_score = min(
        len(relations) * 0.06,
        0.24
    )

    distinct_pairs = set()

    for relation in relations:

        if not isinstance(relation, dict):
            continue

        source = str(
            relation.get("source") or ""
        ).strip()

        target = str(
            relation.get("target") or ""
        ).strip()

        if source and target:
            distinct_pairs.add(
                (source.casefold(), target.casefold())
            )

    source_corroboration = (
        0.04
        if len(distinct_pairs) >= 3
        else 0.00
    )

    try:
        components = int(components or 1)
    except (TypeError, ValueError):
        components = 1

    if connected:
        connectivity_bonus = 0.06
    elif components <= 2:
        connectivity_bonus = 0.02
    else:
        connectivity_bonus = 0.00

    path_bonus = 0.04 if path_exists else 0.00

    contradiction_penalty = min(
        len(contradictions) * 0.12,
        0.34
    )

    score = (
        prior
        + entity_score
        + relation_score
        + source_corroboration
        + connectivity_bonus
        + path_bonus
        - contradiction_penalty
    )

    score = max(0.0, min(score, 1.0))

    return {
        "prior": round(prior, 2),
        "entity_score": round(entity_score, 2),
        "relation_score": round(relation_score, 2),
        "source_corroboration": round(
            source_corroboration,
            2
        ),
        "connectivity_bonus": round(
            connectivity_bonus,
            2
        ),
        "path_bonus": round(path_bonus, 2),
        "path_exists": bool(path_exists),
        "contradiction_penalty": round(
            contradiction_penalty,
            2
        ),
        "confidence": round(score, 2),
        "confidence_percentage": round(
            score * 100,
            1
        ),
        "entity_count": len(entities),
        "relation_count": len(relations),
        "distinct_relation_pairs": len(distinct_pairs),
        "contradiction_count": len(contradictions),
        "connected": bool(connected),
        "components": components,
    }