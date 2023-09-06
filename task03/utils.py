from syntax import Instruction

ARITHMETIC_OPS = 'add', 'mul', 'sub', 'div'
COMPARISON_OPS = 'eq', 'lt', 'gt', 'le', 'ge'
LOGICAL_OPS = 'not', 'and', 'or'

def is_pure(instr: Instruction) -> bool:
    op = instr['op']

    return (
        op in ARITHMETIC_OPS or
        op in COMPARISON_OPS or
        op in LOGICAL_OPS or
        op == 'const' or
        op == 'id'
    )
