#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


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
            cache[name] = tok
        return cache[name]

    @classmethod
    def make_masterpat(cls) -> str:
        return "|".join(f"(?P<{name}>{pat})" for name, pat in cls._masterpat.items())

    def __repr__(self):
        args = ", ".join(f"{k}={v}" for k, v in self.__dict__.items() if k != "name")
        return f"Token({self.name}, {args})"


def test_masterpat():
    Token("LPAREN", pat=r"\(")
    Token("RPAREN", pat=r"\)")
    assert Token.make_masterpat() == "(?P<LPAREN>\\()|(?P<RPAREN>\\))"


def test_lparen():
    tok = Token("LPAREN")
    assert tok is Token("LPAREN")


def test_rparen():
    tok = Token("RPAREN")
    assert tok is Token("RPAREN")


def test_num():
    tok = Token("NUM", pat=r"\d+", val=10.3)
    assert tok is not Token("NUM", pat=r"\d+", val=10.3)
    assert str(tok) == "Token(NUM, pat=\\d+, val=10.3)"
    num2 = Token("NUM", pat=r"\d+", val=2.2)
    assert str(num2) == "Token(NUM, pat=\\d+, val=2.2)"
    num3 = Token("NUM", pat=r"\d+", val=3.3)
    assert str(num3) == "Token(NUM, pat=\\d+, val=3.3)"
    assert num3 is not num2


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
    print(str(tok3))
