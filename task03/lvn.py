import argparse
import json
import sys
from dataclasses import dataclass
from itertools import chain
from typing import Any, NewType, Union

from bb import BasicBlock, flatten_blocks, prog_blocks
from syntax import Instruction, Literal, Program, Type
from tdce import tdce
from utils import is_pure

@dataclass(frozen=True)
class TypedLiteral:
    val: Literal
    type: Type

Vn = NewType('Vn', int)

Value = Union[TypedLiteral, str, tuple[str, tuple[Vn, ...], Any]]
"""A literal value, opaque variable, or operation."""

Table = list[tuple[Value, set[str]]]
"""Map from value numbers to values and variables."""

Context = dict[str, Vn]
Index = dict[Value, Vn]

def canonicalize(val: Value, table: Table) -> Value:
    if isinstance(val, tuple):
        if len(val[1]) == 1:
            op, (arg,), _ = val

            if op == 'id':
                return table[arg][0]
        elif len(val[1]) == 2:
            op, (left, right), extra = val

            if op in ('add', 'mul', 'eq', 'and', 'or'):
                left, right = sorted((left, right))

                return (op, (left, right), extra)

    return val

def canonical_value(
    instr: Instruction, table: Table, context: Context
) -> Value:
    if instr['op'] == 'const':
        assert 'type' in instr
        assert 'value' in instr

        return TypedLiteral(instr['value'], instr['type'])
    else:
        args = tuple(context[arg] for arg in instr.get('args', []))

        funcs = instr.get('funcs', [])
        labels = instr.get('labels', [])

        extra = tuple(chain(funcs, labels))

        return canonicalize((instr['op'], args, extra), table)

def rewrite_args(
    instr: Instruction, table: Table, context: Context
) -> Instruction:
    if 'args' in instr:
        args = instr['args']

        for i, arg in enumerate(args):
            args[i] = min(table[context[arg]][1])

    return instr

def lvn(block: BasicBlock) -> BasicBlock:
    table: Table = []
    context: Context = {}
    index: Index = {}

    result: BasicBlock = []

    for item in block:
        if 'label' in item:
            result.append(item)

            continue

        for arg in item.get('args', []):
            if arg not in context:
                vn = Vn(len(table))
                table.append((arg, {arg}))

                index[arg] = vn
                context[arg] = vn

        if 'dest' in item:
            assert 'type' in item

            dest = item['dest']
            val = canonical_value(item, table, context)

            if val in index and table[index[val]][1] and is_pure(item):
                vn = index[val]
                _, vars = table[vn]

                result.append({
                    'op': 'id',
                    'dest': dest,
                    'type': item['type'],
                    'args': [min(vars)]
                })

                if dest in context:
                    table[context[dest]][1].remove(dest)

                vars.add(dest)
            else:
                result.append(rewrite_args(item, table, context))

                if dest in context:
                    table[context[dest]][1].remove(dest)

                vn = Vn(len(table))
                table.append((val, {dest}))

                index[val] = vn

            context[dest] = vn
        else:
            result.append(rewrite_args(item, table, context))

    return result

def main():
    parser = argparse.ArgumentParser(description='Local value numbering.')

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

        for i, block in enumerate(func_blocks):
            func_blocks[i] = lvn(block)

        func['instrs'] = flatten_blocks(tdce(func_blocks))

    json.dump(prog, sys.stdout)

if __name__ == '__main__':
    main()
