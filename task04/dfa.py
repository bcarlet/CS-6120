from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar

from cfg import CFG, Node

class Direction(Enum):
    FORWARD = 0
    BACKWARD = 1

V = TypeVar('V', bound='Value')

class Value(ABC):
    @classmethod
    @abstractmethod
    def top(cls: type[V]) -> V:
        raise NotImplementedError

    @abstractmethod
    def meet(self: V, other: V) -> None:
        raise NotImplementedError

    @abstractmethod
    def __eq__(self: V, other: V) -> bool:
        raise NotImplementedError

@dataclass
class Framework(Generic[V]):
    dir: Direction
    value: type[V]
    transfer: Callable[[Node, V], V]
    init: V

@dataclass
class DFA(Generic[V]):
    ins: list[V]
    outs: list[V]

class WorkList(OrderedDict):
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)

def dfa(graph: CFG, framework: Framework[V]) -> DFA[V]:
    ins = [framework.init for _ in graph.all]
    outs = [framework.init for _ in graph.all]

    if framework.dir == Direction.FORWARD:
        transfer_in = ins
        transfer_out = outs
    else:
        transfer_in = outs
        transfer_out = ins

    work_list = WorkList.fromkeys(graph.all)

    while work_list:
        node, _ = work_list.popitem(False)

        if framework.dir == Direction.FORWARD:
            predecessors = node.ins
            successors = node.outs
        else:
            predecessors = node.outs
            successors = node.ins

        transfer_in[node.id] = framework.value.top()

        for predecessor in predecessors:
            transfer_in[node.id].meet(transfer_out[predecessor.id])

        new = framework.transfer(node, transfer_in[node.id])

        if new != transfer_out[node.id]:
            transfer_out[node.id] = new

            for successor in successors:
                work_list[successor] = None

    return DFA(ins, outs)
