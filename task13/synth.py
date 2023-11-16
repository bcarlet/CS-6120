import lark
import sys
import z3
from collections import defaultdict
from functools import reduce
from typing import Any

GRAMMAR = """
start: stmts expr

stmts: stmt*

stmt: CNAME ":=" expr ";"

?expr: sum
  | sum "?" sum ":" sum -> if

?sum: term
  | sum "+" term        -> add
  | sum "-" term        -> sub

?term: item
  | term "*"  item      -> mul
  | term "/"  item      -> div
  | term ">>" item      -> shr
  | term "<<" item      -> shl
  | term "^"  item      -> xor

?item: NUMBER           -> num
  | "-" item            -> neg
  | CNAME               -> var
  | "(" expr ")"

%import common.NUMBER
%import common.WS
%import common.CNAME
%ignore WS
""".strip()


def interp(tree, lookup, assign, sequence) -> Any:
    """Evaluate the arithmetic expression.

    Pass a tree as a Lark `Tree` object for the parsed expression. For
    `lookup`, provide a function for mapping variable names to values.
    """

    op = tree.data
    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr', 'xor'):
        lhs = interp(tree.children[0], lookup, assign, sequence)
        rhs = interp(tree.children[1], lookup, assign, sequence)
        if op == 'add':
            return lhs + rhs
        elif op == 'sub':
            return lhs - rhs
        elif op == 'mul':
            return lhs * rhs
        elif op == 'div':
            return lhs / rhs
        elif op == 'shl':
            return lhs << rhs
        elif op == 'shr':
            return lhs >> rhs
        elif op == 'xor':
            return lhs ^ rhs
    elif op == 'neg':
        sub = interp(tree.children[0], lookup, assign, sequence)
        return -sub
    elif op == 'num':
        return int(tree.children[0])
    elif op == 'var':
        return lookup(tree.children[0])
    elif op == 'if':
        cond = interp(tree.children[0], lookup, assign, sequence)
        true = interp(tree.children[1], lookup, assign, sequence)
        false = interp(tree.children[2], lookup, assign, sequence)
        return (cond != 0) * true + (cond == 0) * false
    elif op == 'stmt':
        expr = interp(tree.children[1], lookup, assign, sequence)
        return assign(tree.children[0], expr)
    elif op == 'stmts':
        return sequence(
            interp(child, lookup, assign, sequence) for child in tree.children
        )
    elif op == 'start':
        equalities = interp(tree.children[0], lookup, assign, sequence)
        return interp(tree.children[1], lookup, assign, sequence), equalities


def pretty(tree, subst={}, paren=False):
    """Pretty-print a tree, with optional substitutions applied.

    If `paren` is true, then loose-binding expressions are
    parenthesized. We simplify boolean expressions "on the fly."
    """

    if paren:
        par = lambda s: '({})'.format(s)
    else:
        par = lambda s: s

    op = tree.data
    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr', 'xor'):
        lhs = pretty(tree.children[0], subst, True)
        rhs = pretty(tree.children[1], subst, True)
        c = {
            'add': '+',
            'sub': '-',
            'mul': '*',
            'div': '/',
            'shl': '<<',
            'shr': '>>',
            'xor': '^',
        }[op]
        return par('{} {} {}'.format(lhs, c, rhs))
    elif op == 'neg':
        sub = pretty(tree.children[0], subst)
        return '-{}'.format(sub, True)
    elif op == 'num':
        return tree.children[0]
    elif op == 'var':
        name = tree.children[0]
        return str(subst.get(name, name))
    elif op == 'if':
        cond = pretty(tree.children[0], subst)
        true = pretty(tree.children[1], subst)
        false = pretty(tree.children[2], subst)
        return par('{} ? {} : {}'.format(cond, true, false))
    elif op == 'stmt':
        name = tree.children[0]
        expr = pretty(tree.children[1], subst)
        return '{} := {};\n'.format(subst.get(name, name), expr)
    elif op == 'stmts':
        return ''.join(pretty(child, subst) for child in tree.children)
    elif op == 'start':
        stmts = pretty(tree.children[0], subst)
        expr = pretty(tree.children[1], subst)
        return '{}{}'.format(stmts, expr)


def run(tree, env):
    """Ordinary expression evaluation.

    `env` is a mapping from variable names to values.
    """

    def sequence(stmts):
        for _ in stmts:
            pass

    return interp(tree, env.__getitem__, env.__setitem__, sequence)


def z3_expr(tree, vars=None):
    """Create a Z3 expression from a tree.

    Return the Z3 expression and a dict mapping variable names to all
    free variables occurring in the expression. All variables are
    represented as BitVecs of width 8. Optionally, `vars` can be an
    initial set of variables.
    """

    vars = defaultdict(lambda: [], vars or {})
    current = defaultdict(lambda: 0)

    def new(name):
        v = z3.BitVec('{}{}'.format(name, "'" * len(vars[name])), 8)
        vars[name].append(v)
        current[name] = -1
        return v

    def get_var(name):
        if name in vars:
            return vars[name][current[name]]
        else:
            return new(name)

    def set_var(name, val):
        return new(name) == val

    def sequence(stmts):
        return reduce(z3.And, stmts, True)

    return interp(tree, get_var, set_var, sequence), vars


def solve(phi):
    """Solve a Z3 expression, returning the model."""

    s = z3.Solver()
    s.add(phi)
    s.check()
    return s.model()


def model_values(model):
    """Get the values out of a Z3 model."""

    return {
        d.name(): model[d] for d in model.decls()
    }


def synthesize(tree1, tree2):
    """Given two programs, synthesize the values for holes that make
    them equal.

    `tree1` has no holes. In `tree2`, every variable beginning with the
    letter "h" is considered a hole.
    """

    (expr1, eqs1), vars1 = z3_expr(tree1)
    (expr2, eqs2), vars2 = z3_expr(tree2, vars1)

    plain_vars = [
        var for k, v in vars2.items() for var in v if not k.startswith('h')
    ]

    goal = z3.ForAll(
        plain_vars,
        z3.Implies(z3.And(eqs1, eqs2), expr1 == expr2),
    )

    return solve(goal)


def main(source):
    src1, src2 = source.strip().split('---')

    parser = lark.Lark(GRAMMAR)
    tree1 = parser.parse(src1)
    tree2 = parser.parse(src2)

    model = synthesize(tree1, tree2)

    print(pretty(tree1))
    print('---')
    print(pretty(tree2, model_values(model)))


if __name__ == '__main__':
    main(sys.stdin.read())
