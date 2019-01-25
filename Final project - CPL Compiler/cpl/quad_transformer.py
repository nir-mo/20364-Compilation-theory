import abc

from lark.visitors import Transformer

from cla import CPLTokenizer
from cpl_ast import build_ast
from symbol_table import SymbolTable, Types

__author__ = "Nir Moshe"


class TemporaryVariables(object):
    variables_counter = 0

    @staticmethod
    def get_new_temporary_variable():
        TemporaryVariables.variables_counter += 1
        return "t%d" % TemporaryVariables.variables_counter

    @staticmethod
    def reset():
        TemporaryVariables.variables_counter = 0


class CPLTransformer(Transformer):
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table

    def factor(self, tree):
        return Factor(tree, self.symbol_table)

    def term(self, tree):
        return Term(tree)

    def expression(self, tree):
        return Expression(tree)

    def declarations(self, _):
        return [] # ignore the CPL declarations.


class CPLObject(object):
    __metaclass__ = abc.ABCMeta

    def get_node_type(self):
        return self.NODE_TYPE

    def copy_properties(self, subtree):
        self.type = subtree[0].type
        self.value = subtree[0].value
        self.code = subtree[0].code

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.value)


class Expression(CPLObject):
    NODE_TYPE = "expression"

    def __init__(self, subtree):
        if subtree[0].get_node_type() == Term.NODE_TYPE:
            self.copy_properties(subtree)
        else:
            self.handle_expression(subtree)

    def handle_expression(self, subtree):
        expression = subtree[0]
        operator_token = subtree[1].value
        term = subtree[2]
        self.type = Types.FLOAT if Types.FLOAT in (term.type, expression.type) else Types.INT
        self.value = TemporaryVariables.get_new_temporary_variable()

        # build the code.
        self.code = expression.code + term.code
        self.code.append(ADD(self.value, expression.value, term.value, operator_token, self.type))


class Term(CPLObject):
    NODE_TYPE = "term"

    def __init__(self, subtree):
        if subtree[0].get_node_type() == Factor.NODE_TYPE:
            self.copy_properties(subtree)
        else: #  This is a term.
            self.handle_term(subtree)

    def handle_term(self, subtree):
        term = subtree[0]
        operator_token = subtree[1].value
        factor = subtree[2]
        self.type = Types.FLOAT if Types.FLOAT in (term.type, factor.type) else Types.INT
        self.value = TemporaryVariables.get_new_temporary_variable()

        # build the code.
        self.code = term.code + factor.code
        self.code.append(MLT(self.value, term.value, factor.value, operator_token, self.type))


class Factor(CPLObject):
    NODE_TYPE = "factor"

    def __init__(self, ast_subtree, symbol_table):
        first_token = ast_subtree[0]
        if first_token.type == "NUM":
            self.handle_number(ast_subtree)
        elif first_token.type == "ID":
            self.handle_id(ast_subtree, symbol_table)
        elif first_token.type == "LEFT_PARENTHESIS":
            self.handle_expression(ast_subtree)

    def handle_number(self, ast_subtree):
        self.type = self.get_num_type(ast_subtree[0].value)
        self.value = (
            float(ast_subtree[0].value) if self.type == Types.FLOAT else int(ast_subtree[0].value)
        )
        self.code = []

    def handle_id(self, ast_subtree, symbol_table):
        symbol = symbol_table.get_symbol(ast_subtree[0].value)
        if not symbol:
            raise ValueError("Undefined symbol: %s" % ast_subtree[0].value)

        self.type = symbol.type
        self.value = symbol.name
        self.code = []

    def handle_expression(self, ast_subtree):
        expression = ast_subtree[1]
        self.type = expression.type
        self.value = expression.value
        self.code = expression.code

    @staticmethod
    def get_num_type(number):
        if type(number) == float:
            return Types.FLOAT
        else:
            return Types.INT


class MLT(object):
    def __init__(self, dest, op1, op2, operator, type):
        self.dest, self.op1, self.op2, self.type = dest, op1, op2, type
        self.operator = operator

    @property
    def code(self):
        if self.operator == "*":
            asm_inst = "IMLT" if self.type == Types.INT else "RMLT"
        else:
            asm_inst = "IDIV" if self.type == Types.INT else "RDIV"

        return "%s %s %s %s" % (asm_inst, self.dest, self.op1, self.op2)


class ADD(object):
    def __init__(self, dest, op1, op2, operator, type):
        self.dest, self.op1, self.op2, self.type = dest, op1, op2, type
        self.operator = operator

    @property
    def code(self):
        if self.operator == "+":
            asm_inst = "IADD" if self.type == Types.INT else "RADD"
        else:
            asm_inst = "ISUB" if self.type == Types.INT else "RSUB"

        return "%s %s %s %s" % (asm_inst, self.dest, self.op1, self.op2)


if __name__ == "__main__":
    import sys
    input_filename = sys.argv[1]
    with open(input_filename) as inf:
        ast = build_ast(CPLTokenizer(inf.read()))
        print(ast)
        sym = SymbolTable.build_form_ast(ast)
        c = CPLTransformer(sym)
        #c.transform(ast)


