from syntax import Function, Instruction, Item, Program

def is_term(instr: Instruction) -> bool:
    return instr['op'] in ('jmp', 'br', 'ret')

BasicBlock = list[Item]

def func_blocks(func: Function) -> list[BasicBlock]:
    items = func['instrs']

    blocks: list[BasicBlock] = []
    lead = 0

    for i, item in enumerate(items):
        if 'label' in item:
            if lead < i:
                blocks.append(items[lead:i])

            lead = i
        elif is_term(item):
            blocks.append(items[lead:i + 1])
            lead = i + 1

    if lead < len(items):
        blocks.append(items[lead:])

    return blocks

def prog_blocks(prog: Program) -> dict[str, list[BasicBlock]]:
    return {func['name']: func_blocks(func) for func in prog['functions']}

def flatten_blocks(blocks: list[BasicBlock]) -> list[Item]:
    return [item for block in blocks for item in block]
