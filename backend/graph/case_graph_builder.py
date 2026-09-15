import networkx as nx


def build_case_graph(entities: list, relations: list):
    """
    Build a knowledge graph from entities and relationships.
    """

    graph = nx.Graph()

    # Add entity nodes
    for entity in entities:

        graph.add_node(
            entity["text"],
            type=entity["type"]
        )

    # Add relationship edges
    for relation in relations:

        source = relation["source"]
        target = relation["target"]
        relation_type = relation["relation"]

        graph.add_edge(
            source,
            target,
            relation=relation_type,
            weight=1
        )

    return graph


def graph_to_json(graph):
    """
    Convert NetworkX graph into JSON-friendly format.
    """

    nodes = []

    for node, data in graph.nodes(data=True):

        nodes.append({
            "id": node,
            "type": data.get("type", "UNKNOWN")
        })

    edges = []

    for source, target, data in graph.edges(data=True):

        edges.append({
            "source": source,
            "target": target,
            "relation": data.get("relation", "RELATED"),
            "weight": data.get("weight", 1)
        })

    return {
        "nodes": nodes,
        "edges": edges
    }