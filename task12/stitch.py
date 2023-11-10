import argparse
import json
import sys

def stitch(instrs, trace):
    return [
        *trace,
        {'op': 'ret'},
        {'label': '_abort'},
        *instrs,
    ]

def main():
    parser = argparse.ArgumentParser(
        description='Adds a speculative trace to a function.'
    )

    parser.add_argument(
        'file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin
    )
    parser.add_argument(
        '--trace',
        type=argparse.FileType('r'),
        required=True
    )
    parser.add_argument(
        '--func',
        required=True
    )

    args = parser.parse_args()

    prog = json.load(args.file)
    trace = json.load(args.trace)

    for func in prog['functions']:
        if func['name'] == args.func:
            func['instrs'] = stitch(func['instrs'], trace)

            break

    json.dump(prog, sys.stdout)

if __name__ == '__main__':
    main()
