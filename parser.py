#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator
from typing import get_origin, get_args, Literal
from inspect import signature, _empty
from functools import wraps
import re
import operator
import pytest


def autoassert(func):
    sig = signature(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        for name, parm in sig.parameters.items():
            if (anno := parm.annotation) is not _empty:
                if get_origin(anno) is Literal:
                    lit = get_args(anno)
                    typ = tuple(type(x) for x in lit)
                    val = bound.arguments[name]
                    if not isinstance(val, typ):
                        raise TypeError(
                            f"{name!r} must by of types {tuple(typ.__name__ for typ in typ)}"
                            f", got type {type(val).__name__}"
                        )
                    if val not in lit:
                        raise ValueError(f"{name!r} must be one of {lit}")
                elif not isinstance(bound.arguments[name], anno):
                    raise TypeError(
                        f"{name!r} [{bound.arguments[name]!r}]: must be of type {anno}"
                    )
        res = func(*args, **kwargs)
        return res

    return wrapper


TOKENS = {
    name: f"(?P<{name}>{pat})"
    for name, pat in {
        "PLUS": r"\+",
        "MINUS": r"-",
        "MUL": r"\*",
        "DIV": r"/",
        "LPAREN": r"\(",
        "RPAREN": r"\)",
        "NUM": r"\d+",
        "WS": r"\s+",
    }.items()
}


def masterpat():
    return "|".join(TOKENS.values())


class Token:
    def __init__(self, name: str, val: str = ""):
        self.name = name
        self.val = val

    def __eq__(self, other) -> bool:
        if isinstance(other, Token):
            return self.__dict__ == other.__dict__
        elif isinstance(other, str):
            return self.name == other or self.val == other
        elif issubclass(other, BinOp):
            return self.val == other._op
        else:
            return NotImplemented

    def __repr__(self):
        return f"Token({self.name}, {self.val})"


class Node:
    pass


class Num(Node):
    @autoassert
    def __init__(self, val: float):
        self.val = val

    def __eq__(self, other) -> bool:
        if isinstance(other, Num):
            return self.val == other.val
        else:
            return NotImplemented

    def __repr__(self):
        return f"Num({self.val})"

    def eval(self) -> float:
        return float(self.val)


class BinOp(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __eq__(self, other) -> bool:
        if isinstance(other, type(self)):
            return self.__dict__ == other.__dict__
        else:
            return NotImplemented

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.left)}, {self.right})"

    def eval(self) -> float:
        return self._func(self.left.eval(), self.right.eval())


class Plus(BinOp):
    _op = "+"
    _func = operator.add


class Minus(BinOp):
    _op = "-"
    _func = operator.sub


class Mul(BinOp):
    _op = "*"
    _func = operator.mul


class Div(BinOp):
    _op = "/"
    _func = operator.truediv


class Parser:
    def __init__(self):
        self.tokens: Iterator[Token] | None = None
        self.tok: Token | None = None

    def parse(self, sexpr: str) -> Node:
        self.tokens = iter_tokens(sexpr)
        self._advance()
        return self.expr()

    def expr(self) -> Node:
        res: Node = self.term()
        while (tok := self.tok) in (Plus, Minus):
            self._consume()
            res = {"+": Plus, "-": Minus}[tok.val](res, self.term())
        return res

    def term(self) -> Node:
        res: Node = self.factor()
        while (tok := self.tok) in (Mul, Div):
            self._consume()
            res = {"*": Mul, "/": Div}[tok.val](res, self.factor())
        return res

    def factor(self) -> Node:
        if self.tok == "(":
            self._consume()
            res = self.expr()
            # self._expect(")")
            self._expect(")")
        else:
            res = Num(float(self.tok.val))
            self._consume()
        return res

    def _advance(self) -> Token:
        self.tok = next(self.tokens, None)
        return self.tok

    def _consume(self) -> None:
        self.tok = next(self.tokens, None)

    # @autoassert
    def _expect(self, expected: Token | str) -> None:
        if self.tok != expected:
            raise SyntaxError(f"{expected!r}: was expected, got {self.tok}")
        self._consume()


def iter_tokens(sexpr: str = "") -> Iterator[Token]:
    for match in re.finditer(masterpat(), sexpr):
        if match.lastgroup != "WS":
            yield Token(match.lastgroup, match.group(0))


def test_iter_tokens(capsys):
    for tok in iter_tokens("2 + (3 * 4) + 5"):
        print(tok)
    assert (
        capsys.readouterr().out
        == """\
Token(NUM, 2)
Token(PLUS, +)
Token(LPAREN, ()
Token(NUM, 3)
Token(MUL, *)
Token(NUM, 4)
Token(RPAREN, ))
Token(PLUS, +)
Token(NUM, 5)
"""
    )


@pytest.mark.parametrize(
    "sexpr, expected",
    [
        ("2 + (3 * 4) + 5", 19.0),
    ],
)
def test_parser_eval(sexpr, expected):
    assert Parser().parse(sexpr).eval() == expected


if __name__ == "__main__":
    p = Parser()
    n: Node = p.parse("2 + (3 * 4) + 5")
    # print(n)
    print(n.eval())
