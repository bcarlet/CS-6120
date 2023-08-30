import argparse
import json
import sys

def visit_instruction(instr):
    if 'op' in instr and instr['op'] == 'br':
        instr['labels'].reverse()

def visit_function(func):
    for instr in func['instrs']:
        visit_instruction(instr)

def visit_program(prog):
    for func in prog['functions']:
        visit_function(func)

def main():
    parser = argparse.ArgumentParser(
        description='Swaps the target labels of all conditional branches.'
    )

    parser.add_argument(
        'file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin
    )

    args = parser.parse_args()
    prog = json.load(args.file)

    visit_program(prog)

    json.dump(prog, sys.stdout)

if __name__ == '__main__':
    main()
