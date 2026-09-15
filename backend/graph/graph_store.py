import networkx as nx


# ============================================
# BUILD KNOWLEDGE GRAPH
# ============================================

def build_graph(relations):

    graph = nx.Graph()

    for relation in relations:

        source = relation["source"]

        target = relation["target"]

        relationship = relation["relation"]


        # Add nodes

        graph.add_node(source)

        graph.add_node(target)


        # Add relationship

        graph.add_edge(

            source,

            target,

            relation=relationship,

            weight=1

        )

    return graph


# ============================================
# BFS SEARCH
# ============================================

def bfs_search(graph, start, target):

    if not start or not target:

        return []


    if start not in graph:

        return []


    if target not in graph:

        return []


    try:

        return nx.shortest_path(

            graph,

            start,

            target

        )

    except nx.NetworkXNoPath:

        return []


# ============================================
# DFS SEARCH
# ============================================

def dfs_search(graph, start, target):

    if not start or not target:

        return []


    if start not in graph:

        return []


    if target not in graph:

        return []


    visited = set()

    path = []


    def dfs(node):

        visited.add(node)

        path.append(node)


        # Target found

        if node == target:

            return True


        for neighbour in graph.neighbors(node):

            if neighbour not in visited:

                if dfs(neighbour):

                    return True


        path.pop()

        return False


    if dfs(start):

        return path


    return []


# ============================================
# A* SEARCH
# ============================================

def astar_search(graph, start, target):

    if not start or not target:

        return []


    if start not in graph:

        return []


    if target not in graph:

        return []


    try:

        return nx.astar_path(

            graph,

            start,

            target,

            heuristic=lambda a, b: 0,

            weight="weight"

        )

    except nx.NetworkXNoPath:

        return []


# ============================================
# GRAPH JSON
# ============================================

def graph_json(graph):

    nodes = []


    for node in graph.nodes:

        nodes.append({

            "id": node,

            "type": "ENTITY"

        })


    edges = []


    for source, target, data in graph.edges(
        data=True
    ):

        edges.append({

            "source": source,

            "target": target,

            "relation":
                data.get(
                    "relation",
                    "related"
                )

        })


    return {

        "nodes": nodes,

        "edges": edges

    }