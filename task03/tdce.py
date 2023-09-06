import argparse
import json
import sys

from bb import BasicBlock, flatten_blocks, prog_blocks
from syntax import Item, Program
from utils import is_pure

def globally_used(blocks: list[BasicBlock]) -> set[str]:
    used: set[str] = set()

    for block in blocks:
        for item in block:
            if 'args' in item:
                used.update(item['args'])

    return used

def tdce_block(block: BasicBlock, globally_used: set[str]) -> BasicBlock:
    keep: list[Item] = []
    used = globally_used.copy()

    for item in reversed(block):
        if 'dest' in item:
            dest = item['dest']

            if dest in used or not is_pure(item):
                keep.append(item)
                used.discard(dest)

            if 'args' in item:
                used.update(item['args'])
        else:
            keep.append(item)

    keep.reverse()

    return keep

def tdce(blocks: list[BasicBlock]) -> list[BasicBlock]:
    converged = False
    current = blocks.copy()

    while not converged:
        converged = True
        used = globally_used(current)

        for i, block in enumerate(current):
            new = tdce_block(block, used)

            if len(new) != len(block):
                converged = False

            current[i] = new

    return current

def main():
    parser = argparse.ArgumentParser(
        description='Trivial dead code elimination.'
    )

    parser.add_argument(
        'file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin
    )

    args = parser.parse_args()
    prog: Program = json.load(args.file)

    blocks = prog_blocks(prog)

    for func in prog['functions']:
        name = func['name']
        func_blocks = blocks[name]

        func['instrs'] = flatten_blocks(tdce(func_blocks))

    json.dump(prog, sys.stdout)

if __name__ == '__main__':
    main()
