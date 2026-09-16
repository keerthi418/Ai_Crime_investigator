"""
Graph Store / Search Algorithms
--------------------------------

Provides graph traversal and path-search algorithms
for the AI Crime Investigator.

Supported algorithms:
    - BFS (Breadth-First Search)
    - DFS (Depth-First Search)
    - A* (A-Star Search)

The graph is expected to be a NetworkX graph.

Node names are normalized case-insensitively so that:

    "Ravi"
    "ravi"
    " RAVI "

can refer to the same graph node.
"""

import heapq
from collections import deque


# ============================================================
# NODE NORMALIZATION
# ============================================================

def normalize_node(graph, value):
    """
    Find the actual graph node corresponding to a user-provided
    node value.

    Matching is:
        1. Exact match
        2. Case-insensitive match
        3. Whitespace-normalized match

    Args:
        graph:
            NetworkX graph.

        value:
            Node name supplied by the user.

    Returns:
        Actual graph node if found, otherwise None.
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

    value_lower = value.lower()

    for node in graph.nodes:

        node_text = str(node).strip()

        if node_text.lower() == value_lower:
            return node

    return None


# ============================================================
# BFS
# ============================================================

def bfs(graph, start, target):
    """
    Breadth-First Search.

    BFS finds the shortest path in terms of number
    of edges when all edges have equal cost.

    Args:
        graph:
            NetworkX graph.

        start:
            Starting node.

        target:
            Destination node.

    Returns:
        list:
            Path from start to target.

        Example:
            ["Ravi", "Transaction", "Bank"]
    """

    if graph is None:
        return []

    start = normalize_node(
        graph,
        start
    )

    target = normalize_node(
        graph,
        target
    )

    if start is None or target is None:
        return []

    if start == target:
        return [start]

    # --------------------------------------------------------
    # Queue
    # --------------------------------------------------------

    queue = deque()

    queue.append(
        (
            start,
            [start]
        )
    )

    visited = {start}

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    while queue:

        current, path = queue.popleft()

        # Sort neighbors for deterministic results.
        neighbors = sorted(
            graph.neighbors(current),
            key=lambda node: str(node).lower()
        )

        for neighbor in neighbors:

            if neighbor in visited:
                continue

            new_path = path + [neighbor]

            # Target reached.
            if neighbor == target:
                return new_path

            visited.add(neighbor)

            queue.append(
                (
                    neighbor,
                    new_path
                )
            )

    # No path exists.
    return []


# ============================================================
# DFS
# ============================================================

def dfs(graph, start, target):
    """
    Depth-First Search.

    DFS explores one branch deeply before
    backtracking.

    Args:
        graph:
            NetworkX graph.

        start:
            Starting node.

        target:
            Destination node.

    Returns:
        list:
            Path from start to target.
    """

    if graph is None:
        return []

    start = normalize_node(
        graph,
        start
    )

    target = normalize_node(
        graph,
        target
    )

    if start is None or target is None:
        return []

    # --------------------------------------------------------
    # Stack
    # --------------------------------------------------------

    stack = [
        (
            start,
            [start]
        )
    ]

    visited = set()

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    while stack:

        current, path = stack.pop()

        if current in visited:
            continue

        visited.add(current)

        # Target reached.
        if current == target:
            return path

        # Sort neighbors to make traversal predictable.
        neighbors = sorted(
            graph.neighbors(current),
            key=lambda node: str(node).lower(),
            reverse=True
        )

        for neighbor in neighbors:

            if neighbor in visited:
                continue

            stack.append(
                (
                    neighbor,
                    path + [neighbor]
                )
            )

    # No path exists.
    return []


# ============================================================
# A* SEARCH
# ============================================================

def astar(graph, start, target):
    """
    A* Search.

    Currently all relationships have equal cost,
    so the heuristic is zero.

    Therefore this behaves similarly to Uniform-Cost
    Search / Dijkstra for the current graph.

    The function is kept as A* so that a meaningful
    heuristic can be added later.

    Args:
        graph:
            NetworkX graph.

        start:
            Starting node.

        target:
            Destination node.

    Returns:
        list:
            Path from start to target.
    """

    if graph is None:
        return []

    start = normalize_node(
        graph,
        start
    )

    target = normalize_node(
        graph,
        target
    )

    if start is None or target is None:
        return []

    if start == target:
        return [start]

    # --------------------------------------------------------
    # Heuristic
    # --------------------------------------------------------

    def heuristic(node):
        """
        Current graph has no spatial information.

        Therefore h(n) = 0.

        This keeps the heuristic admissible.
        """

        return 0

    # --------------------------------------------------------
    # Priority Queue
    # --------------------------------------------------------

    open_set = []

    counter = 0

    heapq.heappush(
        open_set,
        (
            heuristic(start),
            0,
            counter,
            start,
            [start]
        )
    )

    # Best known cost from start.
    best_cost = {
        start: 0
    }

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    while open_set:

        (
            _,
            cost,
            _,
            current,
            path
        ) = heapq.heappop(open_set)

        # Ignore stale queue entries.
        if cost > best_cost.get(
            current,
            float("inf")
        ):
            continue

        # Target reached.
        if current == target:
            return path

        neighbors = sorted(
            graph.neighbors(current),
            key=lambda node: str(node).lower()
        )

        for neighbor in neighbors:

            # Every edge currently has cost 1.
            new_cost = cost + 1

            if (
                neighbor not in best_cost
                or new_cost < best_cost[neighbor]
            ):

                best_cost[neighbor] = new_cost

                counter += 1

                priority = (
                    new_cost
                    + heuristic(neighbor)
                )

                heapq.heappush(
                    open_set,
                    (
                        priority,
                        new_cost,
                        counter,
                        neighbor,
                        path + [neighbor]
                    )
                )

    # No path exists.
    return []


# ============================================================
# RUN ALL SEARCH ALGORITHMS
# ============================================================

def run_search_algorithms(
    graph,
    start,
    target
):
    """
    Run BFS, DFS and A* on the same graph.

    Returns:

        {
            "BFS": [...],
            "DFS": [...],
            "A*": [...]
        }
    """

    if graph is None:
        return {
            "BFS": [],
            "DFS": [],
            "A*": []
        }

    return {
        "BFS": bfs(
            graph,
            start,
            target
        ),

        "DFS": dfs(
            graph,
            start,
            target
        ),

        "A*": astar(
            graph,
            start,
            target
        )
    }


# ============================================================
# PATH FORMATTING
# ============================================================

def path_to_string(path):
    """
    Convert a path into a readable string.

    Example:

        ["Ravi", "Phone", "Chennai"]

    becomes:

        "Ravi -> Phone -> Chennai"
    """

    if not path:
        return "No path found"

    return " -> ".join(
        str(node)
        for node in path
    )


# ============================================================
# SEARCH SUMMARY
# ============================================================

def get_search_summary(
    graph,
    start,
    target
):
    """
    Run all algorithms and return a structured summary.

    Useful for API responses and frontend display.
    """

    results = run_search_algorithms(
        graph,
        start,
        target
    )

    return {
        "start": normalize_node(
            graph,
            start
        ),

        "target": normalize_node(
            graph,
            target
        ),

        "BFS": results["BFS"],

        "DFS": results["DFS"],

        "A*": results["A*"],

        "BFS_text": path_to_string(
            results["BFS"]
        ),

        "DFS_text": path_to_string(
            results["DFS"]
        ),

        "A*_text": path_to_string(
            results["A*"]
        )
    }