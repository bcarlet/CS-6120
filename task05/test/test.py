import json
import sys
from collections import deque

from bb import prog_blocks
from cfg import CFG, Node
from dom import DomTree, dom_frontier, dom_tree, dominators
from syntax import Program

def is_dominator(a: Node, b: Node, graph: CFG) -> bool:
    if a.id == graph.entry.id:
        return True

    queue = deque([graph.entry])
    discovered = {graph.entry.id}

    while queue:
        node = queue.popleft()

        if node.id == b.id:
            return False

        for successor in node.outs:
            if successor.id not in discovered and successor.id != a.id:
                discovered.add(node.id)
                queue.append(successor)

    return True

def check_dominators(dom: list[set[Node]], graph: CFG):
    universe = set(graph.all)

    for node in graph.all:
        for dominator in dom[node.id]:
            assert is_dominator(dominator, node, graph)

        for other in universe.difference(dom[node.id]):
            assert not is_dominator(other, node, graph)

def is_immediate_dominator(a: Node, b: Node, dom: list[set[Node]]) -> bool:
    if a not in dom[b.id] or a.id == b.id:
        return False

    for dominator in dom[b.id]:
        if a in dom[dominator.id] and a.id != dominator.id != b.id:
            return False

    return True

def check_dom_tree(tree: list[DomTree], graph: CFG):
    dom = dominators(graph)

    for node in tree:
        if node.parent is None:
            assert node.node.id == graph.entry.id
        else:
            assert is_immediate_dominator(node.parent.node, node.node, dom)

        for child in node.children:
            assert is_immediate_dominator(node.node, child.node, dom)

        for other in graph.all:
            if other.id not in (child.node.id for child in node.children):
                assert not is_immediate_dominator(node.node, other, dom)

def in_dominance_frontier(a: Node, b: Node, dom: list[set[Node]]) -> bool:
    if b in dom[a.id] and b.id != a.id:
        return False

    for predecessor in a.ins:
        if b in dom[predecessor.id]:
            return True

    return False

def check_dom_frontier(frontier: list[set[Node]], graph: CFG):
    universe = set(graph.all)
    dom = dominators(graph)

    for node in graph.all:
        for front in frontier[node.id]:
            assert in_dominance_frontier(front, node, dom)

        for other in universe.difference(frontier[node.id]):
            assert not in_dominance_frontier(other, node, dom)

def main():
    prog: Program = json.load(sys.stdin)
    blocks = prog_blocks(prog)

    for func in prog['functions']:
        graph = CFG.from_blocks(blocks[func['name']])

        dom = dominators(graph)
        tree = dom_tree(graph, dom)
        frontier = dom_frontier(graph, dom)

        try:
            check_dominators(dom, graph)
            check_dom_tree(tree, graph)
            check_dom_frontier(frontier, graph)
        except AssertionError:
            print('result: fail')
            exit()

    print('result: pass')

if __name__ == '__main__':
    main()
