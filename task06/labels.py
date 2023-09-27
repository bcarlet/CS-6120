from bb import BasicBlock

class LabelGenerator:
    def __init__(self, blocks: list[BasicBlock]):
        self.used = {
            block[0]['label'] for block in blocks if 'label' in block[0]
        }
        self.count = 0

    def next(self) -> str:
        while (label := f'anonymous{self.count}') in self.used:
            self.count += 1

        self.count += 1

        return label

def insert_labels(blocks: list[BasicBlock], gen: LabelGenerator):
    for block in blocks:
        if 'label' not in block[0]:
            block.insert(0, {'label': gen.next()})

def get_label(block: BasicBlock) -> str:
    assert 'label' in block[0]

    return block[0]["label"]
