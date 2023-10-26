import argparse
import json
import sys

def is_free(item) -> bool:
    return 'op' in item and item['op'] == 'free'

def main():
    parser = argparse.ArgumentParser(
        description='Removes all `free` instructions.'
    )

    parser.add_argument(
        'file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin
    )

    args = parser.parse_args()
    prog = json.load(args.file)

    for func in prog['functions']:
        func['instrs'] = [item for item in func['instrs'] if not is_free(item)]

    json.dump(prog, sys.stdout)

if __name__ == '__main__':
    main()
