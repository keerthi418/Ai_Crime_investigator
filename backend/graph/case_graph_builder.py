"""
Knowledge Graph Builder
-----------------------

Converts extracted entities and relationships into
a clean NetworkX knowledge graph.

Pipeline:

    NER
     ↓
    Entities
     ↓
    Relation Extraction
     ↓
    Relationships
     ↓
    Knowledge Graph
     ↓
    BFS / DFS / A*

Graph structure:

    ENTITY
       |
       | relationship
       ↓
    ENTITY
"""

import networkx as nx


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

        return str(
            entity.get("text")
            or entity.get("label")
            or entity.get("name")
            or ""
        ).strip()

    return str(entity).strip()


def _type(entity):
    """
    Extract entity type safely.
    """

    if isinstance(entity, dict):

        return str(
            entity.get("type")
            or "ENTITY"
        ).strip().upper()

    return "ENTITY"


# ============================================================
# NODE NORMALIZATION
# ============================================================

def _find_existing_node(graph, value):
    """
    Find an existing graph node using case-insensitive
    comparison.

    Example:

        Graph contains "Ravi Kumar"

        Input:
            "ravi kumar"

        Returns:
            "Ravi Kumar"
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # Exact match first.
    if value in graph.nodes:
        return value

    value_lower = value.lower()

    for node in graph.nodes:

        if str(node).strip().lower() == value_lower:
            return node

    return None


def _canonical_node(graph, value):
    """
    Return the canonical graph node for a value.

    If an equivalent node already exists, use it.
    Otherwise return the cleaned value.
    """

    value = str(value or "").strip()

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
    Extract relation source safely.
    """

    if not isinstance(relation, dict):
        return ""

    return str(
        relation.get("source")
        or relation.get("from")
        or ""
    ).strip()


def _relation_target(relation):
    """
    Extract relation target safely.
    """

    if not isinstance(relation, dict):
        return ""

    return str(
        relation.get("target")
        or relation.get("to")
        or ""
    ).strip()


def _relation_label(relation):
    """
    Extract relation label safely.
    """

    if not isinstance(relation, dict):
        return "related_to"

    return str(
        relation.get("relation")
        or relation.get("label")
        or "related_to"
    ).strip()


# ============================================================
# BUILD CASE GRAPH
# ============================================================

def build_case_graph(
    entities=None,
    relations=None
):
    """
    Build a NetworkX knowledge graph.

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

        label = _text(entity)

        if not label:
            continue

        entity_type = _type(entity)

        existing_node = _find_existing_node(
            graph,
            label
        )

        if existing_node is not None:

            # Preserve the original canonical label.
            graph.nodes[existing_node]["label"] = (
                graph.nodes[existing_node].get(
                    "label",
                    existing_node
                )
            )

            # Upgrade generic type if a real type is available.
            if (
                graph.nodes[existing_node].get("type")
                == "ENTITY"
                and entity_type != "ENTITY"
            ):
                graph.nodes[existing_node]["type"] = entity_type

            continue

        graph.add_node(
            label,
            label=label,
            type=entity_type
        )

    # ========================================================
    # 2. ADD RELATIONSHIP EDGES
    # ========================================================

    for relation in relations:

        if not isinstance(relation, dict):
            continue

        source = _relation_source(
            relation
        )

        target = _relation_target(
            relation
        )

        relationship = _relation_label(
            relation
        )

        if not source or not target:
            continue

        # ----------------------------------------------------
        # Map relation endpoints to existing entity nodes.
        # ----------------------------------------------------

        source_node = _canonical_node(
            graph,
            source
        )

        target_node = _canonical_node(
            graph,
            target
        )

        if source_node is None or target_node is None:
            continue

        # ----------------------------------------------------
        # If relation endpoint wasn't already present as an
        # NER entity, add it as a generic entity.
        #
        # This keeps the graph usable even if the relation
        # extractor found a valid entity that NER missed.
        # ----------------------------------------------------

        if source_node not in graph.nodes:

            graph.add_node(
                source_node,
                label=source_node,
                type="ENTITY"
            )

        if target_node not in graph.nodes:

            graph.add_node(
                target_node,
                label=target_node,
                type="ENTITY"
            )

        # ----------------------------------------------------
        # Avoid self-loop relationships.
        # ----------------------------------------------------

        if source_node == target_node:
            continue

        # ----------------------------------------------------
        # Add edge.
        # ----------------------------------------------------

        graph.add_edge(
            source_node,
            target_node,
            label=relationship,
            relation=relationship
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
    """

    if graph is None:
        return {
            "nodes": [],
            "edges": []
        }

    nodes = []

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

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
                            "ENTITY"
                        )
                    )
                }
            }
        )

    # --------------------------------------------------------
    # Edges
    # --------------------------------------------------------

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
            or "related_to"
        )

        edges.append(
            {
                "data": {
                    "id": f"edge-{index}",

                    "source": str(
                        source
                    ),

                    "target": str(
                        target
                    ),

                    "label": relationship,

                    "relation": relationship
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

    Useful for the dashboard.
    """

    if graph is None:

        return {
            "node_count": 0,
            "edge_count": 0,
            "connected": False,
            "component_count": 0
        }

    return {
        "node_count": graph.number_of_nodes(),

        "edge_count": graph.number_of_edges(),

        "connected": (
            nx.is_connected(graph)
            if graph.number_of_nodes() > 0
            else False
        ),

        "component_count": (
            nx.number_connected_components(graph)
            if graph.number_of_nodes() > 0
            else 0
        )
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
    """

    if graph is None:
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

    except nx.NetworkXError:

        return False