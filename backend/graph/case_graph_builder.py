"""
Knowledge Graph Builder
-----------------------

AI Crime Investigator knowledge graph module.

Pipeline:

    NER
      ↓
    Entities
      ↓
    Relation Extraction
      ↓
    Relationships
      ↓
    NetworkX Knowledge Graph
      ↓
    BFS / DFS / A*

Graph structure:

    ENTITY
       |
       | relationship
       ↓
    ENTITY

This module is responsible for:

    - Creating NetworkX graphs
    - Normalizing entity names
    - Adding entity metadata
    - Adding relationship metadata
    - Preserving relationship reasons
    - Converting graphs to frontend/Cytoscape JSON
    - Graph statistics
    - Path checking
"""


import networkx as nx


# ============================================================
# DEFAULT VALUES
# ============================================================

DEFAULT_ENTITY_TYPE = "ENTITY"
DEFAULT_RELATIONSHIP = "related_to"
DEFAULT_REASON = "Relationship detected from case evidence."


# ============================================================
# ENTITY HELPERS
# ============================================================

def _text(entity):
    """
    Extract entity text safely.

    Supported formats:

        {"text": "Ravi", "type": "PERSON"}

        {"label": "Ravi", "type": "PERSON"}

        {"name": "Ravi", "type": "PERSON"}

        "Ravi"
    """

    if entity is None:
        return ""

    if isinstance(entity, dict):

        value = (
            entity.get("text")
            or entity.get("label")
            or entity.get("name")
            or ""
        )

        return str(value).strip()

    return str(entity).strip()


def _type(entity):
    """
    Extract entity type safely.

    Example:

        PERSON
        LOCATION
        ORGANIZATION
        DATE
        PHONE
        EMAIL
        ENTITY
    """

    if isinstance(entity, dict):

        value = (
            entity.get("type")
            or entity.get("entity_type")
            or DEFAULT_ENTITY_TYPE
        )

        value = str(value).strip().upper()

        return value or DEFAULT_ENTITY_TYPE

    return DEFAULT_ENTITY_TYPE


# ============================================================
# NODE NORMALIZATION
# ============================================================

def _find_existing_node(graph, value):
    """
    Find an existing graph node using case-insensitive
    comparison.

    Example:

        Graph contains:
            "Ravi Kumar"

        Input:
            "ravi kumar"

        Returns:
            "Ravi Kumar"
    """

    if graph is None:
        return None

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    if value in graph.nodes:
        return value

    # --------------------------------------------------------
    # Case-insensitive match
    # --------------------------------------------------------

    value_lower = value.casefold()

    for node in graph.nodes:

        if str(node).strip().casefold() == value_lower:
            return node

    return None


def _canonical_node(graph, value):
    """
    Return the canonical graph node for a value.

    If an equivalent node already exists, its original
    spelling is preserved.

    Otherwise the cleaned value is returned.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    existing = _find_existing_node(
        graph,
        value
    )

    if existing is not None:
        return existing

    return value


# ============================================================
# RELATION HELPERS
# ============================================================

def _relation_source(relation):
    """
    Extract relationship source safely.

    Supported:

        source
        from
    """

    if not isinstance(relation, dict):
        return ""

    value = (
        relation.get("source")
        or relation.get("from")
        or ""
    )

    return str(value).strip()


def _relation_target(relation):
    """
    Extract relationship target safely.

    Supported:

        target
        to
    """

    if not isinstance(relation, dict):
        return ""

    value = (
        relation.get("target")
        or relation.get("to")
        or ""
    )

    return str(value).strip()


def _relation_label(relation):
    """
    Extract relationship label safely.

    Supported:

        relation
        label

    Example:

        knows
        owns
        contacted
        located_at
        related_to
    """

    if not isinstance(relation, dict):
        return DEFAULT_RELATIONSHIP

    value = (
        relation.get("relation")
        or relation.get("label")
        or DEFAULT_RELATIONSHIP
    )

    value = str(value).strip()

    return value or DEFAULT_RELATIONSHIP


def _relation_reason(relation):
    """
    Extract the explanation/reason for a relationship.

    This value is displayed by the frontend inside
    the green Relationship Reason box.
    """

    if not isinstance(relation, dict):
        return DEFAULT_REASON

    value = (
        relation.get("reason")
        or relation.get("explanation")
        or relation.get("evidence")
        or ""
    )

    value = str(value).strip()

    return value or DEFAULT_REASON


# ============================================================
# ADD / MERGE ENTITY NODE
# ============================================================

def _add_entity_node(
    graph,
    entity
):
    """
    Add an entity to the graph.

    If the entity already exists using a different
    capitalization, the existing canonical node is reused.

    Returns:

        canonical node name
    """

    label = _text(entity)

    if not label:
        return None

    entity_type = _type(entity)

    existing_node = _find_existing_node(
        graph,
        label
    )

    # --------------------------------------------------------
    # Existing entity
    # --------------------------------------------------------

    if existing_node is not None:

        existing_type = graph.nodes[
            existing_node
        ].get(
            "type",
            DEFAULT_ENTITY_TYPE
        )

        # Upgrade generic ENTITY type when a
        # more specific type becomes available.
        if (
            existing_type == DEFAULT_ENTITY_TYPE
            and entity_type != DEFAULT_ENTITY_TYPE
        ):
            graph.nodes[
                existing_node
            ]["type"] = entity_type

        return existing_node

    # --------------------------------------------------------
    # New entity
    # --------------------------------------------------------

    graph.add_node(
        label,
        label=label,
        type=entity_type
    )

    return label


# ============================================================
# ADD / MERGE RELATIONSHIP
# ============================================================

def _add_relationship(
    graph,
    relation
):
    """
    Add a relationship between two graph nodes.

    If NER missed one of the endpoints, the endpoint is
    automatically added as a generic ENTITY.

    Returns:

        True  -> relationship added
        False -> relationship ignored
    """

    if not isinstance(relation, dict):
        return False

    source = _relation_source(
        relation
    )

    target = _relation_target(
        relation
    )

    relationship = _relation_label(
        relation
    )

    reason = _relation_reason(
        relation
    )

    if not source or not target:
        return False

    # --------------------------------------------------------
    # Resolve canonical nodes.
    # --------------------------------------------------------

    source_node = _canonical_node(
        graph,
        source
    )

    target_node = _canonical_node(
        graph,
        target
    )

    if source_node is None or target_node is None:
        return False

    # --------------------------------------------------------
    # Avoid self relationships.
    # --------------------------------------------------------

    if source_node == target_node:
        return False

    # --------------------------------------------------------
    # Add missing source endpoint.
    # --------------------------------------------------------

    if source_node not in graph.nodes:

        graph.add_node(
            source_node,
            label=source_node,
            type=DEFAULT_ENTITY_TYPE
        )

    # --------------------------------------------------------
    # Add missing target endpoint.
    # --------------------------------------------------------

    if target_node not in graph.nodes:

        graph.add_node(
            target_node,
            label=target_node,
            type=DEFAULT_ENTITY_TYPE
        )

    # --------------------------------------------------------
    # Existing edge
    # --------------------------------------------------------

    if graph.has_edge(
        source_node,
        target_node
    ):

        edge_data = graph[
            source_node
        ][
            target_node
        ]

        existing_relation = edge_data.get(
            "relation",
            DEFAULT_RELATIONSHIP
        )

        existing_reason = edge_data.get(
            "reason",
            DEFAULT_REASON
        )

        # ----------------------------------------------------
        # If another relationship label exists, preserve both.
        # ----------------------------------------------------

        if (
            relationship
            and relationship != existing_relation
        ):

            labels = set()

            for value in str(
                existing_relation
            ).split(" | "):

                if value.strip():
                    labels.add(
                        value.strip()
                    )

            labels.add(
                relationship
            )

            edge_data["relation"] = " | ".join(
                sorted(labels)
            )

            edge_data["label"] = edge_data[
                "relation"
            ]

        # ----------------------------------------------------
        # Preserve a useful reason.
        # ----------------------------------------------------

        if (
            reason
            and reason != DEFAULT_REASON
        ):

            if (
                not existing_reason
                or existing_reason == DEFAULT_REASON
            ):
                edge_data["reason"] = reason

            elif reason not in existing_reason:
                edge_data["reason"] = (
                    f"{existing_reason} {reason}"
                )

        return True

    # --------------------------------------------------------
    # New edge
    # --------------------------------------------------------

    graph.add_edge(
        source_node,
        target_node,
        label=relationship,
        relation=relationship,
        reason=reason
    )

    return True


# ============================================================
# BUILD CASE GRAPH
# ============================================================

def build_case_graph(
    entities=None,
    relations=None
):
    """
    Build a NetworkX undirected knowledge graph.

    Args:

        entities:
            Extracted NER entities.

        relations:
            Extracted entity-to-entity relationships.

    Returns:

        networkx.Graph
    """

    graph = nx.Graph()

    entities = entities or []
    relations = relations or []

    # ========================================================
    # 1. ADD ENTITY NODES
    # ========================================================

    for entity in entities:

        _add_entity_node(
            graph,
            entity
        )

    # ========================================================
    # 2. ADD RELATIONSHIP EDGES
    # ========================================================

    for relation in relations:

        _add_relationship(
            graph,
            relation
        )

    return graph


# ============================================================
# CREATE CASE GRAPH
# ============================================================

def create_case_graph(
    entities=None,
    relations=None
):
    """
    Backward-compatible wrapper for build_case_graph().
    """

    return build_case_graph(
        entities,
        relations
    )


# ============================================================
# GRAPH -> JSON
# ============================================================

def graph_to_json(graph):
    """
    Convert NetworkX graph into Cytoscape-compatible JSON.

    Returns:

        {
            "nodes": [...],
            "edges": [...]
        }

    Node example:

        {
            "data": {
                "id": "Ravi",
                "label": "Ravi",
                "type": "PERSON"
            }
        }

    Edge example:

        {
            "data": {
                "id": "edge-0",
                "source": "Ravi",
                "target": "Chennai",
                "label": "located_at",
                "relation": "located_at",
                "reason": "Evidence connects Ravi with Chennai."
            }
        }
    """

    if graph is None:

        return {
            "nodes": [],
            "edges": []
        }

    nodes = []

    # ========================================================
    # NODES
    # ========================================================

    for node, data in graph.nodes(
        data=True
    ):

        node_id = str(node)

        nodes.append(
            {
                "data": {
                    "id": node_id,
                    "label": str(
                        data.get(
                            "label",
                            node_id
                        )
                    ),
                    "type": str(
                        data.get(
                            "type",
                            DEFAULT_ENTITY_TYPE
                        )
                    )
                }
            }
        )

    # ========================================================
    # EDGES
    # ========================================================

    edges = []

    for index, (
        source,
        target,
        data
    ) in enumerate(
        graph.edges(
            data=True
        )
    ):

        relationship = str(
            data.get(
                "relation"
            )
            or data.get(
                "label"
            )
            or DEFAULT_RELATIONSHIP
        )

        reason = str(
            data.get(
                "reason"
            )
            or DEFAULT_REASON
        )

        edges.append(
            {
                "data": {
                    "id": f"edge-{index}",
                    "source": str(source),
                    "target": str(target),
                    "label": relationship,
                    "relation": relationship,
                    "reason": reason
                }
            }
        )

    return {
        "nodes": nodes,
        "edges": edges
    }


# ============================================================
# GET GRAPH DATA
# ============================================================

def get_graph_data(graph):
    """
    Backward-compatible wrapper for graph_to_json().
    """

    return graph_to_json(
        graph
    )


# ============================================================
# GRAPH STATISTICS
# ============================================================

def get_graph_statistics(graph):
    """
    Return basic graph statistics.

    Useful for:

        - Dashboard
        - Investigation results
        - Reports
        - Graph analysis
    """

    if graph is None:

        return {
            "node_count": 0,
            "edge_count": 0,
            "connected": False,
            "component_count": 0
        }

    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()

    if node_count == 0:

        return {
            "node_count": 0,
            "edge_count": 0,
            "connected": False,
            "component_count": 0
        }

    component_count = nx.number_connected_components(
        graph
    )

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "connected": component_count == 1,
        "component_count": component_count
    }


# ============================================================
# FIND PATH
# ============================================================

def graph_has_path(
    graph,
    start,
    target
):
    """
    Check whether a path exists between two nodes.

    Matching is case-insensitive.
    """

    if graph is None:
        return False

    if graph.number_of_nodes() == 0:
        return False

    start_node = _find_existing_node(
        graph,
        start
    )

    target_node = _find_existing_node(
        graph,
        target
    )

    if start_node is None or target_node is None:
        return False

    try:

        return nx.has_path(
            graph,
            start_node,
            target_node
        )

    except (
        nx.NetworkXError,
        nx.NodeNotFound
    ):

        return False


# ============================================================
# FIND SHORTEST PATH
# ============================================================

def find_shortest_path(
    graph,
    start,
    target
):
    """
    Find the shortest path between two nodes.

    Returns:

        list of nodes

    Example:

        [
            "Ravi",
            "Kumar",
            "Chennai"
        ]

    Returns an empty list when no path exists.
    """

    if graph is None:
        return []

    start_node = _find_existing_node(
        graph,
        start
    )

    target_node = _find_existing_node(
        graph,
        target
    )

    if start_node is None or target_node is None:
        return []

    try:

        return nx.shortest_path(
            graph,
            start_node,
            target_node
        )

    except (
        nx.NetworkXError,
        nx.NodeNotFound
    ):

        return []


# ============================================================
# GET NODE INFORMATION
# ============================================================

def get_node_information(
    graph,
    node
):
    """
    Return information about a graph node.

    Returns:

        {
            "id": ...,
            "label": ...,
            "type": ...,
            "degree": ...
        }

    Returns None when the node does not exist.
    """

    if graph is None:
        return None

    canonical_node = _find_existing_node(
        graph,
        node
    )

    if canonical_node is None:
        return None

    data = graph.nodes[
        canonical_node
    ]

    return {
        "id": str(canonical_node),
        "label": str(
            data.get(
                "label",
                canonical_node
            )
        ),
        "type": str(
            data.get(
                "type",
                DEFAULT_ENTITY_TYPE
            )
        ),
        "degree": graph.degree(
            canonical_node
        )
    }


# ============================================================
# GET RELATIONSHIP INFORMATION
# ============================================================

def get_relationship_information(
    graph,
    source,
    target
):
    """
    Return relationship information between two nodes.

    Returns None when no relationship exists.
    """

    if graph is None:
        return None

    source_node = _find_existing_node(
        graph,
        source
    )

    target_node = _find_existing_node(
        graph,
        target
    )

    if source_node is None or target_node is None:
        return None

    if not graph.has_edge(
        source_node,
        target_node
    ):
        return None

    data = graph[
        source_node
    ][
        target_node
    ]

    return {
        "source": str(source_node),
        "target": str(target_node),
        "relation": str(
            data.get(
                "relation",
                DEFAULT_RELATIONSHIP
            )
        ),
        "label": str(
            data.get(
                "label",
                DEFAULT_RELATIONSHIP
            )
        ),
        "reason": str(
            data.get(
                "reason",
                DEFAULT_REASON
            )
        )
    }


# ============================================================
# GET GRAPH SUMMARY
# ============================================================

def get_graph_summary(graph):
    """
    Return a frontend/report-friendly graph summary.
    """

    statistics = get_graph_statistics(
        graph
    )

    if graph is None:
        degree_values = []

    else:
        degree_values = [
            degree
            for _, degree
            in graph.degree()
        ]

    maximum_degree = (
        max(degree_values)
        if degree_values
        else 0
    )

    return {
        "nodes": statistics["node_count"],
        "relationships": statistics["edge_count"],
        "connected": statistics["connected"],
        "components": statistics["component_count"],
        "maximum_node_degree": maximum_degree
    }