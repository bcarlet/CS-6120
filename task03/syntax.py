from typing import TypedDict, Union

Type = Union[str, dict[str, 'Type']]
Literal = Union[bool, int]

class Label(TypedDict):
    label: str

class _InstructionBase(TypedDict):
    op: str

class Instruction(_InstructionBase, total=False):
    dest: str
    type: Type
    args: list[str]
    funcs: list[str]
    labels: list[str]
    value: Literal

Item = Union[Label, Instruction]

class Argument(TypedDict):
    name: str
    type: Type

class _FunctionBase(TypedDict):
    name: str
    instrs: list[Item]

class Function(_FunctionBase, total=False):
    args: list[Argument]
    type: Type

class Program(TypedDict):
    functions: list[Function]
