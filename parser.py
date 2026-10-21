#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator
import re
import operator
import pytest

# from typeguard import typechecked


class Token:
    _cache = {}
    _masterpat = {}

    def __new__(cls, name, *args, **kwargs):
        cache = __class__._cache
        masterpat = __class__._masterpat
        if name not in cache:
            tok = super().__new__(cls)
            tok.name = name
            tok.__dict__.update(kwargs)
            if "pat" in kwargs:
                if name not in masterpat:
                    masterpat[name] = kwargs["pat"]
            if name == "NUM":  # do not cache NUM token
                return tok
            if not hasattr(tok, "val"):
                setattr(tok, "val", "")
            cache[name] = tok
        return cache[name]

    @classmethod
    def make_masterpat(cls) -> str:
        return "|".join(f"(?P<{name}>{pat})" for name, pat in cls._masterpat.items())

    def __repr__(self):
        args = ", ".join(f"{k}={v}" for k, v in self.__dict__.items() if k != "name")
        return f"Token({self.name}, {args})"


PLUS = Token("PLUS", pat=r"\+")
MINUS = Token("MINUS", pat=r"-")
MUL = Token("MUL", pat=r"\*")
DIV = Token("DIV", pat=r"/")
LPAREN = Token("LPAREN", pat=r"\(")
RPAREN = Token("RPAREN", pat=r"\)")
NUM = Token("NUM", pat=r"\d+")
WS = Token("WS", pat=r"\s+")


class Node:
    @classmethod
    def get_node(cls, tok: Token):
        return cls.op_to_node[tok.val]

    op_to_node = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "_op"):
            __class__.op_to_node[cls._op] = cls


class Num(Node):
    # @typechecked
    def __init__(self, tok: Token):
        assert isinstance(tok, Token)
        self.val = float(tok.val)

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

    def while_in_tokens(self, func, tokens) -> Node:
        res: Node = func()
        while (tok := self.tok) in tokens:
            self._consume()
            res = Node.get_node(tok)(res, func())
        return res

    def expr(self) -> Node:
        return self.while_in_tokens(self.term, (PLUS, MINUS))

    def term(self) -> Node:
        return self.while_in_tokens(self.factor, (MUL, DIV))

    def factor(self) -> Node:
        if self.tok == LPAREN:
            self._consume()
            res = self.expr()
            self._expect(RPAREN)
        else:
            res = Num(self.tok)
            self._consume()
        return res

    def _advance(self) -> Token:
        self.tok = next(self.tokens, None)
        return self.tok

    def _consume(self) -> None:
        self.tok = next(self.tokens, None)

    # @typechecked
    def _expect(self, expected: Token) -> None:
        if self.tok != expected:
            raise SyntaxError(f"{expected!r}: was expected, got {self.tok}")
        self._consume()


def iter_tokens(sexpr: str = "") -> Iterator[Token]:
    for match in re.finditer(Token.make_masterpat(), sexpr):
        if match.lastgroup != "WS":
            yield Token(match.lastgroup, val=match.group(0))


def test_iter_tokens(capsys):
    for tok in iter_tokens("2 + (3 * 4) + 5"):
        print(tok)
    assert (
        capsys.readouterr().out
        == """\
Token(NUM, val=2)
Token(PLUS, pat=\\+, val=)
Token(LPAREN, pat=\\(, val=)
Token(NUM, val=3)
Token(MUL, pat=\\*, val=)
Token(NUM, val=4)
Token(RPAREN, pat=\\), val=)
Token(PLUS, pat=\\+, val=)
Token(NUM, val=5)
"""
    )


@pytest.mark.parametrize(
    "sexpr",
    [
        "2 + (3 * 4) + 5",
        "9 + (4 * 5) + 3",
        "6 + (4 * 7) + 2",
        "(9 - 4) * 3 + 2",
        "(9 - 3) / 2 + (4 * 5)",
    ],
)
def test_parser_eval(sexpr):
    expected = eval(sexpr)
    assert Parser().parse(sexpr).eval() == expected


if __name__ == "__main__":
    p = Parser()
    n: Node = p.parse("2 + (3 * 4) + 5")
    # print(n)
    print(n.eval())
