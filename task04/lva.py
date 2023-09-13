from dataclasses import dataclass

from cfg import CFG, Node
from dfa import dfa, DFA, Direction, Framework, Value

@dataclass(eq=False)
class LiveVars(Value):
    vars: set[str]

    @classmethod
    def top(cls):
        return cls(set())

    def meet(self: 'LiveVars', other: 'LiveVars'):
        self.vars.update(other.vars)

    def __eq__(self: 'LiveVars', other: 'LiveVars') -> bool:
        return self.vars == other.vars

    def __str__(self) -> str:
        return ', '.join(sorted(self.vars))

@dataclass(init=False)
class Transfer:
    gen: list[set[str]]
    kill: list[set[str]]

    def __init__(self, graph: CFG) -> None:
        self.gen = [set() for _ in graph.all]
        self.kill = [set() for _ in graph.all]

        for i, node in enumerate(graph.all):
            for item in reversed(node.block):
                if 'dest' in item:
                    self.gen[i].discard(item['dest'])
                    self.kill[i].add(item['dest'])

                if 'args' in item:
                    self.gen[i].update(item['args'])

    def __call__(self, node: Node, arg: LiveVars) -> LiveVars:
        vars = arg.vars.difference(self.kill[node.id])
        vars.update(self.gen[node.id])

        return LiveVars(vars)

def lva(graph: CFG) -> DFA[LiveVars]:
    framework = Framework(
        Direction.BACKWARD,
        LiveVars,
        Transfer(graph),
        LiveVars(set())
    )

    return dfa(graph, framework)
