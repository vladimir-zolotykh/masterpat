#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator
import re


class Node:
    pass


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
    def __init__(self, name: str, pat: str):
        self.name = name
        self.pat = pat

    def __repr__(self):
        return self.name


def iter_tokens(sexpr: str = "") -> Iterator[Token]:
    for match in re.finditer(masterpat(), sexpr):
        if match.lastgroup != "WS":
            yield Token(match.lastgroup, match.group(1))


if __name__ == "__main__":
    for tok in iter_tokens("2 + (3 * 4) + 5"):
        print(tok)
