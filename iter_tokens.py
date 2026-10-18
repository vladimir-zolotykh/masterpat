#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator
from typing import get_origin, get_args
from inspect import signature, _empty
from functools import wraps
import re


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
                    raise TypeError(f"{name!r} must be of type {anno}")
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

    def __repr__(self):
        return f"Token({self.name}, {self.val})"


class Node:
    pass


class Num(Node):
    @autoassert
    def __init__(self, val: float):
        self.val = val

    def __eq__(self, other):
        if isinstance(other, Num):
            return self.val == other.val
        else:
            return NotImplemented

    def __repr__(self):
        return f"Num({self.val})"


class BinOp(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.__dict__ == other.__dict__
        else:
            return NotImplemented

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.left)}, {self.right})"


class Plus(BinOp):
    pass


class Minus(BinOp):
    pass


class Mul(BinOp):
    pass


class Div(BinOp):
    pass


class Parser:
    def __init__(self):
        self.tokens = None
        self.tok = None

    def expr(self) -> Node:
        res: Node = self.term()
        while (tok := self.tok) in (Plus, Minus):
            self._consume()
            res = {"+": Plus, "-": Minus}[tok](res, self.term())
        return res

    def term(self) -> Node:
        res: Node = self.factor()
        while (tok := self.tok) in (Mul, Div):
            self._consume()
            res = {}[tok](res, self.factor())
        return res

    def factor(self) -> Node:
        if self.tok == "(":
            self._consume()
            res = self.expr()
            self._expect(")")
        else:
            res = Num(self.tok)
            self._consume()
        return res

    def _advance(self) -> Token:
        self.tok = next(self.tokens, None)
        return self.tok

    def _consume(self) -> None:
        self.tok = next(self.tokens, None)

    def _expect(self, expected: Token) -> None:
        if self.tok != expected:
            raise SyntaxError(f"{expected!r}: was expected, got {self.tok}")
        self._consume()


def iter_tokens(sexpr: str = "") -> Iterator[Token]:
    for match in re.finditer(masterpat(), sexpr):
        if match.lastgroup != "WS":
            yield Token(match.lastgroup, match.group(0))


if __name__ == "__main__":
    for tok in iter_tokens("2 + (3 * 4) + 5"):
        print(tok)
