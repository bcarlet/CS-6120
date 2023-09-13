from dataclasses import dataclass
from typing import NamedTuple

from cfg import CFG, Node
from dfa import dfa, DFA, Direction, Framework, Value
from syntax import Instruction

class Definition(NamedTuple):
    row: int
    col: int

    @classmethod
    def from_instr(cls, instr: Instruction):
        assert 'pos' in instr

        return cls(instr['pos']['row'], instr['pos']['col'])

    def __str__(self) -> str:
        return f'{self.row}:{self.col}'

@dataclass(eq=False)
class ReachingDefs(Value):
    defs: set[Definition]

    @classmethod
    def top(cls):
        return cls(set())

    def meet(self: 'ReachingDefs', other: 'ReachingDefs'):
        self.defs.update(other.defs)

    def __eq__(self: 'ReachingDefs', other: 'ReachingDefs') -> bool:
        return self.defs == other.defs

    def __str__(self) -> str:
        return ', '.join(map(str, sorted(self.defs)))

@dataclass(init=False)
class Transfer:
    gen: list[set[Definition]]
    kill: list[set[Definition]]

    def __init__(self, graph: CFG) -> None:
        self.gen = [set() for _ in graph.all]
        self.kill = [set() for _ in graph.all]

        defs: dict[str, set[Definition]] = {}

        for node in graph.all:
            for item in node.block:
                if 'dest' in item:
                    var_defs = defs.setdefault(item['dest'], set())
                    var_defs.add(Definition.from_instr(item))

        for i, node in enumerate(graph.all):
            for item in node.block:
                if 'dest' in item:
                    self.gen[i].difference_update(defs[item['dest']])
                    self.gen[i].add(Definition.from_instr(item))

                    self.kill[i].update(defs[item['dest']])

    def __call__(self, node: Node, arg: ReachingDefs) -> ReachingDefs:
        defs = arg.defs.difference(self.kill[node.id])
        defs.update(self.gen[node.id])

        return ReachingDefs(defs)

def rda(graph: CFG) -> DFA[ReachingDefs]:
    framework = Framework(
        Direction.FORWARD,
        ReachingDefs,
        Transfer(graph),
        ReachingDefs(set())
    )

    return dfa(graph, framework)
