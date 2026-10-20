#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


class Token:
    _cache = {}

    def __new__(cls, name, *args, **kwargs):
        print(f"__new__ {name = }, {args = }, {kwargs = }")
        cache = __class__._cache
        if name not in cache:
            tok = super().__new__(cls)
            tok.name = name
            tok.__dict__.update(kwargs)
            if name == "NUM":  # do not cache NUM token
                return tok
            cache[name] = tok
        return cache[name]

    def __init__(self, name: str, *args, **kwargs):
        print(f"__init__ {name = }, {args = }, {kwargs = }")

    def __repr__(self):
        args = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if k != "name")
        return f"Token({self.name}, {args})"
        pass


def test_lparen():
    tok = Token("LPAREN")
    assert tok is Token("LPAREN")


def test_rparen():
    tok = Token("RPAREN")
    assert tok is Token("RPAREN")


def test_num():
    tok = Token("NUM", pat=r"\d+", val=10.3)
    assert tok is not Token("NUM", pat=r"\d+", val=10.3)
    # assert str(tok) == "Token('NUM', pat=r'\\d+', val=10.3)"


if __name__ == "__main__":
    tok1 = Token("LPAREN", pat=r"\(", val="(")
    print(tok1.__dict__)
    tok2 = Token("LPAREN", pat=r"\)", val=")")
    print(tok2.__dict__)
    assert tok1 is tok2
    tok3 = Token("NUM", pat=r"\d+", val=6.3)
    print(tok3.__dict__)
    tok3 = Token("NUM", pat=r"\d+", val=10.3)
    print(tok3.__dict__)
    print(repr(tok3))
