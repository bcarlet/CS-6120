import argparse
import json
import sys
from typing import Any, Callable

from bb import prog_blocks
from dfa import CFG, DFA
from lva import lva
from rda import rda
from syntax import Program

def get_analysis(name: str) -> Callable[[CFG], DFA[Any]]:
    return {
        'lva': lva,
        'rda': rda
    }[name]

def main():
    parser = argparse.ArgumentParser(description='Data-flow analysis.')

    parser.add_argument(
        'file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin
    )
    parser.add_argument(
        '--analysis',
        choices=('lva', 'rda'),
        default='lva'
    )

    args = parser.parse_args()

    prog: Program = json.load(args.file)
    analysis = get_analysis(args.analysis)

    blocks = prog_blocks(prog)
    anon = 0

    for func in prog['functions']:
        name = func['name']
        func_blocks = blocks[name]

        dfa = analysis(CFG.from_blocks(func_blocks))

        for ins, outs, block in zip(dfa.ins, dfa.outs, func_blocks):
            if 'label' in block[0]:
                label = block[0]['label']
            else:
                label = f'anonymous{anon}'
                anon += 1

            print(f'@{name}.{label}:')
            print(f'  ins: {ins}')
            print(f'  outs: {outs}')

if __name__ == '__main__':
    main()
