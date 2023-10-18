from itertools import chain
from typing import Generator

from cfg import CFG, Node
from dom import dominators

def backward_dfs(node: Node, visited: set[int]) -> Generator[Node, None, None]:
    if node.id not in visited:
        visited.add(node.id)

        for predecessor in node.ins:
            yield from backward_dfs(predecessor, visited)

        yield node

def back_edges(graph: CFG) -> list[tuple[Node, Node]]:
    dom = dominators(graph)
    edges: list[tuple[Node, Node]] = []

    for node in graph.all:
        for successor in node.outs:
            if successor in dom[node.id]:
                edges.append((node, successor))

    return edges

def natural_loops(graph: CFG) -> list[list[Node]]:
    edges = back_edges(graph)
    loops: list[list[Node]] = []

    for t, h in edges:
        loops.append(list(chain((h,), backward_dfs(t, {h.id}))))

    return loops
