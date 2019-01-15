from collections import namedtuple

from lark.visitors import Visitor

from exceptions import CPLException, CPLCompoundException
from lark_utils import is_lark_token

__author__ = "Nir Moshe"


Symbol = namedtuple("Symbol", field_names=["name", "type", "line"])


class SymbolAlreadyExistsError(CPLException):
    def __init__(self, first_symbol, redefinition_symbol_name, line):
        self.first_symbol = first_symbol
        self.redefinition_symbol_name = redefinition_symbol_name


class Types:
    INT = "Integer"
    FLOAT = "Floating point"


class SymbolTable(object):
    def __init__(self):
        self.symbols = {}

    def add_symbol(self, name, type, line):
        if name in self.symbols:
            raise SymbolAlreadyExistsError(self.symbols[name], name, line)

        self.symbols[name] = Symbol(name, type, line)


class SymbolTableBuilder(Visitor):
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self._init_declarations()
        self.errors = []

    def _init_declarations(self):
        self._current_declaration_ids = []
        self._current_declaration_type = None

    def declaration(self, _):
        for token in self._current_declaration_ids:
            try:
                self.symbol_table.add_symbol(
                    name=token.value,
                    type=self._current_declaration_type,
                    line=token.line
                )
            except SymbolAlreadyExistsError as exception:
                self.errors.append(exception)

        self._init_declarations()

    def idlist(self, tree):
        # Collect all the variables definitions.
        for token in tree.children:
            if is_lark_token(token) and token.type == "ID":
                self._current_declaration_ids.append(token)

    def type(self, tree):
        # Extract the variables type (from the declarations statement).
        type_token = tree.children[0]
        if type_token.type == "INT":
            self._current_declaration_type = Types.INT

        else: # It has to be a float.. otherwise lark would have raise an exception.
            self._current_declaration_type = Types.FLOAT

    @classmethod
    def build_form_ast(cls, cpl_ast):
        symbol_table = SymbolTable()
        builder = cls(symbol_table)
        builder.visit(cpl_ast)
        if builder.errors:
            raise CPLCompoundException(builder.errors)

        return symbol_table
