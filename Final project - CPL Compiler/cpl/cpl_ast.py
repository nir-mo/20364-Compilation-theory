# Generates an AST using Lark parser and CLA (CPL tokenizer).
# Author: Nir Moshe.
# Date: 4-Jan-2019
import os

from lark import Lark
from lark.lexer import Lexer, Token as LarkToken

from cla import CPLTokenizer

__author__ = "Nir Moshe"


class CLALexerAdapter(Lexer):
    def __init__(self, *args, **kwargs):
        Lexer.__init__(self)
        self.errors = []

    def lex(self, data):
        for token, line in data:
            if token.name == CPLTokenizer.INVALID_TOKEN_NAME:
                self.errors.append(token)
            else:
                yield LarkToken(token.name, value=token.attribute, line=line)

    def has_lexical_errors(self):
        return len(self.errors) > 0


def build_ast(tokens):
    # TODO: add try-except for unexpected tokens...
    # TODO: Read th cla errors some how.
    # TODO: Handle errors...
    parser = get_default_cpl_parser()
    tree = parser.parse(tokens)
    return tree


def get_default_cpl_parser():
    with open(os.path.join(os.path.dirname(__file__), "cpl.y")) as CPLSyntax:
        return Lark(CPLSyntax.read(), parser="lalr", lexer=CLALexerAdapter)
