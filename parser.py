#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator
import re
import operator
import pytest
from typeguard import typechecked


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
        if other is None:
            return NotImplemented
        elif isinstance(other, Token):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other or self.val == other
        # elif issubclass(other, BinOp):
        #     return self.val == other._op
        elif hasattr(other, "_op"):
            return self.val == other._op
        else:
            return NotImplemented

    def __repr__(self):
        return f"Token({self.name}, {self.val})"


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


PLUS = Token("PLUS")
MINUS = Token("MINUS")
MUL = Token("MUL")
DIV = Token("DIV")
LPAREN = Token("LPAREN")
RPAREN = Token("RPAREN")


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
        # while (tok := self.tok) and tok in (PLUS, MINUS):
        while (tok := self.tok) in (PLUS, MINUS):
            self._consume()
            # res = Node.op_to_node[tok](res, self.term())
            res = Node.get_node(tok)(res, self.term())
        return res

    def term(self) -> Node:
        res: Node = self.factor()
        while (tok := self.tok) in (MUL, DIV):
            self._consume()
            # res = Node.op_to_node[tok.val](res, self.term())
            res = Node.get_node(tok)(res, self.factor())
        return res

    def factor(self) -> Node:
        if self.tok == LPAREN:
            self._consume()
            res = self.expr()
            self._expect(RPAREN)
        else:
            # res = Num(float(self.tok.val))
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
