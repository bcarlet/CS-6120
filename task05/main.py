import argparse
import json
import sys
from typing import Iterable

from bb import BasicBlock, prog_blocks
from cfg import CFG, Node
from dom import dom_frontier, dom_tree, dominators
from syntax import Program

def insert_labels(blocks: list[BasicBlock]):
    used = {block[0]['label'] for block in blocks if 'label' in block[0]}
    count = 0

    for block in blocks:
        if 'label' not in block[0]:
            while (label := f'anonymous{count}') in used:
                count += 1

            block.insert(0, {'label': label})
            count += 1

def get_label(block: BasicBlock, func: str) -> str:
    assert 'label' in block[0]

    return f'@{func}.{block[0]["label"]}'

def dump(
    sets: Iterable[Iterable[Node]],
    blocks: list[BasicBlock],
    func: str
):
    json.dump({
        get_label(block, func): [
            get_label(node.block, func) for node in nodes
        ] for nodes, block in zip(sets, blocks)
    }, sys.stdout, indent=2, sort_keys=True)

def main():
    parser = argparse.ArgumentParser(description='Dominance utilities.')

    parser.add_argument(
        'file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin
    )
    parser.add_argument(
        '--analysis',
        choices=('dom', 'tree', 'front'),
        default='dom'
    )

    args = parser.parse_args()
    prog: Program = json.load(args.file)

    blocks = prog_blocks(prog)

    for func in prog['functions']:
        name = func['name']
        func_blocks = blocks[name]

        insert_labels(func_blocks)

        graph = CFG.from_blocks(func_blocks)
        dom = dominators(graph)

        if args.analysis == 'dom':
            dump(dom, func_blocks, name)
        elif args.analysis == 'tree':
            adj = (
                (child.node for child in node.children)
                    for node in dom_tree(graph, dom)
            )

            dump(adj, func_blocks, name)
        else:
            dump(dom_frontier(graph, dom), func_blocks, name)

        print()

if __name__ == '__main__':
    main()
