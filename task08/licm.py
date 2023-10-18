import argparse
import json
import sys
from itertools import islice

from bb import flatten_blocks, func_blocks
from cfg import CFG, Node
from dom import dominators
from labels import get_label, insert_labels, LabelGenerator
from lva import lva
from nat import natural_loops
from rda import Definition, rda
from syntax import Program
from utils import is_pure

def add_preheader(graph: CFG, loop: list[Node], gen: LabelGenerator) -> Node:
    header = loop[0]
    ins = [node for node in header.ins if node not in loop]

    header_label = get_label(header.block)
    pre_label = gen.next()

    pre = Node(header.id, [{'label': pre_label}], ins, [header])

    for node in ins:
        last = node.block[-1]

        if 'labels' in last:
            last['labels'] = [
                pre_label if label == header_label else label
                    for label in last['labels']
            ]
        elif node.id + 1 != pre.id:
            node.block.append({'op': 'jmp', 'labels': [pre_label]})

        for i, successor in enumerate(node.outs):
            if successor.id == header.id:
                node.outs[i] = pre

    header.ins = [pre] + [node for node in header.ins if node not in ins]

    for node in islice(graph.all, header.id, None):
        node.id += 1

    graph.all.insert(pre.id, pre)

    if pre.id == 0:
        graph.entry = pre
    else:
        before = graph.all[pre.id - 1]

        if before not in ins and 'labels' not in before.block[-1]:
            before.block.append({'op': 'jmp', 'labels': [header_label]})

    return pre

def loop_exits(loop: list[Node]) -> set[Node]:
    exits: set[Node] = set()

    for node in loop:
        for successor in node.outs:
            if successor not in loop:
                exits.add(successor)

    return exits

def licm(graph: CFG, loop: list[Node], gen: LabelGenerator):
    pre = add_preheader(graph, loop, gen)

    reaching = rda(graph)
    live = lva(graph)
    exits = loop_exits(loop)
    dom = dominators(graph)

    li: list[Definition] = []

    def is_arg_invariant(var: str, node: Node, idx: int) -> bool:
        for i in range(idx - 1, -1, -1):
            item = node.block[i]

            if 'dest' in item and item['dest'] == var:
                definition = Definition(var, node, id(item))

                return definition in li

        defs = reaching.ins[node.id].defs

        for definition in defs:
            if definition.var == var and definition.node in loop:
                if len(defs) == 1:
                    return definition in li
                else:
                    return False

        return True

    def is_invariant(node: Node, idx: int) -> bool:
        instr = node.block[idx]

        if 'args' not in instr:
            return True

        for arg in instr['args']:
            if not is_arg_invariant(arg, node, idx):
                return False

        return True

    changed = True

    while changed:
        changed = False

        for node in loop:
            for i, item in enumerate(node.block):
                if 'dest' in item and is_pure(item) and is_invariant(node, i):
                    definition = Definition(item['dest'], node, id(item))

                    if definition not in li:
                        li.append(definition)
                        changed = True

    def is_unique(definition: Definition) -> bool:
        for node in loop:
            for item in node.block:
                if (id(item) != definition.instr
                        and 'dest' in item and item['dest'] == definition.var):
                    return False

        return True

    def dominates_live_exits(definition: Definition) -> bool:
        for exit in exits:
            if (definition.node not in dom[exit.id]
                    and definition.var in live.ins[exit.id].vars):
                return False

        return True

    for definition in reversed(li):
        if (definition.var not in live.outs[pre.id].vars
                and is_unique(definition)
                and dominates_live_exits(definition)):
            for i, item in enumerate(definition.node.block):
                if id(item) == definition.instr:
                    pre.block.insert(1, definition.node.block[i])
                    definition.node.block.pop(i)

                    break
            else:
                raise RuntimeError

def main():
    parser = argparse.ArgumentParser(
        description='Loop-invariant code motion.'
    )

    parser.add_argument(
        'file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin
    )

    args = parser.parse_args()
    prog: Program = json.load(args.file)

    for func in prog['functions']:
        blocks = func_blocks(func)
        graph = CFG.from_blocks(blocks)
        gen = LabelGenerator(blocks)

        insert_labels(blocks, gen)

        headers: set[Node] = set()

        while True:
            for loop in natural_loops(graph):
                if loop[0] not in headers:
                    headers.add(loop[0])
                    licm(graph, loop, gen)

                    break
            else:
                break

        func['instrs'] = flatten_blocks([node.block for node in graph.all])

    json.dump(prog, sys.stdout)

if __name__ == '__main__':
    main()
