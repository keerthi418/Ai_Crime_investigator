"""Reliable graph search algorithms for AI Crime Investigator."""
from collections import deque
import heapq
import time


def normalize_node(graph, value):
    if graph is None or value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    if value in graph.nodes:
        return value
    low = value.casefold()
    for node in graph.nodes:
        if str(node).strip().casefold() == low:
            return node
    return None


def _path(parent, start, target):
    if target not in parent:
        return []
    out=[]
    cur=target
    while cur is not None:
        out.append(cur)
        if cur == start:
            out.reverse()
            return out
        cur=parent.get(cur)
    return []


def bfs(graph, start, target):
    start=normalize_node(graph,start); target=normalize_node(graph,target)
    if start is None or target is None: return []
    if start==target: return [start]
    q=deque([start]); visited={start}; parent={start:None}
    while q:
        cur=q.popleft()
        for nxt in sorted(graph.neighbors(cur), key=lambda x:str(x).casefold()):
            if nxt in visited: continue
            visited.add(nxt); parent[nxt]=cur
            if nxt==target: return _path(parent,start,target)
            q.append(nxt)
    return []


def dfs(graph, start, target):
    start=normalize_node(graph,start); target=normalize_node(graph,target)
    if start is None or target is None: return []
    if start==target: return [start]
    stack=[start]; visited=set(); parent={start:None}
    while stack:
        cur=stack.pop()
        if cur in visited: continue
        visited.add(cur)
        if cur==target: return _path(parent,start,target)
        neighbors=sorted(graph.neighbors(cur), key=lambda x:str(x).casefold(), reverse=True)
        for nxt in neighbors:
            if nxt not in visited:
                if nxt not in parent: parent[nxt]=cur
                stack.append(nxt)
    return []


def astar(graph, start, target):
    start=normalize_node(graph,start); target=normalize_node(graph,target)
    if start is None or target is None: return []
    if start==target: return [start]
    # No domain coordinates exist, so h(n)=0 is the correct admissible heuristic.
    def h(_): return 0
    heap=[(h(start),0,0,start)]
    parent={start:None}; g={start:0}; counter=0
    while heap:
        _,cost,_,cur=heapq.heappop(heap)
        if cost != g.get(cur): continue
        if cur==target: return _path(parent,start,target)
        for nxt in sorted(graph.neighbors(cur), key=lambda x:str(x).casefold()):
            new=cost+1
            if new < g.get(nxt,float('inf')):
                g[nxt]=new; parent[nxt]=cur; counter+=1
                heapq.heappush(heap,(new+h(nxt),new,counter,nxt))
    return []


def run_search_algorithms(graph,start,target):
    return {'BFS':bfs(graph,start,target),'DFS':dfs(graph,start,target),'A*':astar(graph,start,target)}


# ============================================================
# STRUCTURED SEARCH METRICS
# ============================================================
#
# Each function returns a dict of the form:
#
#     {
#         "algorithm": "BFS",
#         "found": True,
#         "path": ["A", "B", "C"],
#         "path_length": 3,
#         "visited_nodes": 4,
#         "execution_time_ms": 0.123,
#         "cost": 2,             # only A*
#         "heuristic_used": "...",  # only A*
#     }
#
# The heuristic h(n) = 0 is used for A* because no domain
# coordinates exist; h(n)=0 is admissible so the search still
# finds shortest paths for the unweighted investigation graph.


def _bfs_counted(graph, start, target):
    start = normalize_node(graph, start)
    target = normalize_node(graph, target)
    if start is None or target is None:
        return [], 0
    if start == target:
        return [start], 1
    q = deque([start])
    visited = {start}
    parent = {start: None}
    visits = 1
    while q:
        cur = q.popleft()
        for nxt in sorted(graph.neighbors(cur), key=lambda x: str(x).casefold()):
            if nxt in visited:
                continue
            visited.add(nxt)
            parent[nxt] = cur
            visits += 1
            if nxt == target:
                return _path(parent, start, target), visits
            q.append(nxt)
    return [], visits


def _dfs_counted(graph, start, target):
    start = normalize_node(graph, start)
    target = normalize_node(graph, target)
    if start is None or target is None:
        return [], 0
    if start == target:
        return [start], 1
    stack = [start]
    visited = set()
    parent = {start: None}
    visits = 0
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        visits += 1
        if cur == target:
            return _path(parent, start, target), visits
        neighbors = sorted(
            graph.neighbors(cur),
            key=lambda x: str(x).casefold(),
            reverse=True,
        )
        for nxt in neighbors:
            if nxt not in visited:
                if nxt not in parent:
                    parent[nxt] = cur
                stack.append(nxt)
    return [], visits


def _astar_counted(graph, start, target):
    start = normalize_node(graph, start)
    target = normalize_node(graph, target)
    if start is None or target is None:
        return [], 0, 0
    if start == target:
        return [start], 1, 0
    def h(_):
        return 0
    heap = [(h(start), 0, 0, start)]
    parent = {start: None}
    g = {start: 0}
    counter = 0
    visits = 0
    while heap:
        _, cost, _, cur = heapq.heappop(heap)
        if cost != g.get(cur):
            continue
        visits += 1
        if cur == target:
            return _path(parent, start, target), visits, cost
        for nxt in sorted(graph.neighbors(cur), key=lambda x: str(x).casefold()):
            new = cost + 1
            if new < g.get(nxt, float('inf')):
                g[nxt] = new
                parent[nxt] = cur
                counter += 1
                heapq.heappush(heap, (new + h(nxt), new, counter, nxt))
    return [], visits, 0


def _detail(algorithm, path, visited_nodes, execution_time_ms, **extra):
    result = {
        "algorithm": algorithm,
        "found": bool(path),
        "path": path,
        "path_length": len(path),
        "visited_nodes": visited_nodes,
        "execution_time_ms": round(execution_time_ms, 4),
    }
    result.update(extra)
    return result


def bfs_details(graph, start, target):
    started = time.perf_counter()
    path, visited_nodes = _bfs_counted(graph, start, target)
    elapsed = (time.perf_counter() - started) * 1000.0
    return _detail("BFS", path, visited_nodes, elapsed)


def dfs_details(graph, start, target):
    started = time.perf_counter()
    path, visited_nodes = _dfs_counted(graph, start, target)
    elapsed = (time.perf_counter() - started) * 1000.0
    return _detail("DFS", path, visited_nodes, elapsed)


def astar_details(graph, start, target):
    started = time.perf_counter()
    path, visited_nodes, cost = _astar_counted(graph, start, target)
    elapsed = (time.perf_counter() - started) * 1000.0
    return _detail(
        "A*",
        path,
        visited_nodes,
        elapsed,
        cost=(len(path) - 1) if path else 0,
        heuristic_used="h(n)=0 (admissible)",
    )


def run_search_details(graph, start, target):
    """
    Run BFS, DFS and A* and return structured metrics for each.
    """
    start_node = normalize_node(graph, start)
    target_node = normalize_node(graph, target)
    return {
        "BFS": bfs_details(graph, start, target),
        "DFS": dfs_details(graph, start, target),
        "A*": astar_details(graph, start, target),
        "start": start_node,
        "target": target_node,
        "algorithm_pair": {
            "start": start_node,
            "target": target_node,
        },
    }


def path_to_string(path):
    return 'No path found' if not path else ' -> '.join(map(str,path))


def get_search_summary(graph,start,target):
    r=run_search_algorithms(graph,start,target)
    return {'start':normalize_node(graph,start),'target':normalize_node(graph,target),
            'BFS':r['BFS'],'DFS':r['DFS'],'A*':r['A*'],
            'BFS_text':path_to_string(r['BFS']),'DFS_text':path_to_string(r['DFS']),
            'A*_text':path_to_string(r['A*'])}
