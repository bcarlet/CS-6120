from dataclasses import dataclass

from bb import BasicBlock

@dataclass(eq=False)
class Node:
    id: int
    block: BasicBlock
    ins: list['Node']
    outs: list['Node']

def successors(i: int, nodes: list[Node], labels: dict[str, Node]):
    last = nodes[i].block[-1]

    if 'labels' in last:
        return [labels[label] for label in last['labels']]

    if 'op' in last and last['op'] == 'ret' or i + 1 == len(nodes):
        return []

    return [nodes[i + 1]]

def is_exit(i: int, nodes: list[Node]):
    last = nodes[i].block[-1]

    if 'op' in last:
        if last['op'] == 'ret':
            return True
        elif last['op'] in ('jmp', 'br'):
            return False

    return i + 1 == len(nodes)

@dataclass
class CFG:
    entry: Node
    exits: list[Node]
    all: list[Node]

    @classmethod
    def from_blocks(cls, blocks: list[BasicBlock]):
        nodes = [Node(id, block, [], []) for id, block in enumerate(blocks)]
        exits = []

        labels = {
            node.block[0]['label']: node
                for node in nodes if 'label' in node.block[0]
        }

        for i, node in enumerate(nodes):
            node.outs = successors(i, nodes, labels)

            for successor in node.outs:
                successor.ins.append(node)

            if is_exit(i, nodes):
                exits.append(node)

        return cls(nodes[0], exits, nodes)
