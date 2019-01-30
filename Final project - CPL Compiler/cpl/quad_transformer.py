import abc

from lark.visitors import Transformer

from cla import CPLTokenizer
from cpl_ast import build_ast
from exceptions import CPLException, CPLCompoundException
from symbol_table import SymbolTable, Types

__author__ = "Nir Moshe"


class SemanticError(CPLException):
    """Represents semantic exception during building the IR."""
    def __init__(self, line, message):
        CPLException.__init__(self, line, message)


class TemporaryVariables(object):
    variables_counter = 0

    @staticmethod
    def get_new_temporary_variable():
        TemporaryVariables.variables_counter += 1
        return "t%d" % TemporaryVariables.variables_counter

    @staticmethod
    def reset():
        TemporaryVariables.variables_counter = 0


class Label(object):
    labels_counter = 0

    def __init__(self, prefix=""):
        self.name = "%s_label_%d" % (prefix, Label.labels_counter)
        Label.labels_counter += 1

    @property
    def code(self):
        return self.name + ":"

    @staticmethod
    def reset():
        Label.labels_counter = 0


def handle_semantic_error(func):
    def wraps(self, tree):
        cpl_object = func(self, tree)
        try:
            self.errors.extend(cpl_object.errors)
        finally:
            return cpl_object

    return wraps


class CPLTransformer(Transformer):
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.errors = []

    @handle_semantic_error
    def factor(self, tree):
        return Factor(tree, self.symbol_table)

    @handle_semantic_error
    def term(self, tree):
        return Term(tree)

    @handle_semantic_error
    def expression(self, tree):
        return Expression(tree)

    @handle_semantic_error
    def boolfactor(self, tree):
        return BoolFactor(tree)

    @handle_semantic_error
    def boolterm(self, tree):
        return BoolTerm(tree)

    @handle_semantic_error
    def boolexpr(self, tree):
        return BoolExpr(tree)

    @handle_semantic_error
    def input_stmt(self, tree):
        return InputStatement(tree, self.symbol_table)

    @handle_semantic_error
    def output_stmt(self, tree):
        return OutputStatement(tree)

    @handle_semantic_error
    def assignment_stmt(self, tree):
        return AssignmentStmt(tree, self.symbol_table)

    @handle_semantic_error
    def cast_stmt(self, tree):
        return CastStmt(tree, self.symbol_table)

    @handle_semantic_error
    def type(self, tree):
        return Types.INT if tree[0].type == "INT" else Types.FLOAT

    @handle_semantic_error
    def if_stmt(self, tree):
        return IfStmt(tree)

    @handle_semantic_error
    def stmt(self, tree):
        return Stmt(tree)

    @handle_semantic_error
    def break_stmt(self, tree):
        return BreakStmt(tree)

    @handle_semantic_error
    def continue_stmt(self, tree):
        return ContinueStmt(tree)

    @handle_semantic_error
    def stmt_block(self, tree):
        return StmtBlock(tree)

    @handle_semantic_error
    def stmtlist(self, tree):
        return StmtList(tree)

    @handle_semantic_error
    def while_stmt(self, tree):
        return WhileStmt(tree)

    @handle_semantic_error
    def caselist(self, tree):
        return Caselist(tree, self.symbol_table)

    @handle_semantic_error
    def switch_stmt(self, tree):
        return SwitchStmt(tree)

    @handle_semantic_error
    def start(self, tree):
        return Program(tree)


class CPLObject(object):
    __metaclass__ = abc.ABCMeta

    def get_node_type(self):
        return self.NODE_TYPE

    @staticmethod
    def get_subtree_node_type(subtree):
        try:
            return subtree[0].get_node_type()
        except AttributeError:
            return None

    def copy_properties_of_node(self, subtree, index=0):
        self.type = subtree[index].type
        self.value = subtree[index].value
        self.code = subtree[index].code

    def handle_binary_operation(self, subtree):
        left = subtree[0]
        operator_token = subtree[1].value
        right = subtree[2]
        self.handle_binary_operation_default_values(subtree)
        self.code.append(QUADInstruction(self.value, left.value, right.value, operator_token, self.type))

    def handle_binary_operation_default_values(self, subtree):
        left = subtree[0]
        right = subtree[2]
        self.value = TemporaryVariables.get_new_temporary_variable()

        if left.type == right.type:
            self.type = left.type
            conversion_code = []
        else:
            self.type = Types.FLOAT
            temp = TemporaryVariables.get_new_temporary_variable()
            if left.type == Types.INT:
                conversion_code = [QUADInstruction(temp, left.value, "", "CAST_TO_REAL", Types.INT)]
                left.value = temp
            else:
                conversion_code = [QUADInstruction(temp, right.value, "", "CAST_TO_REAL", Types.INT)]
                right.value = temp

        # build the code.
        self.code = left.code + right.code + conversion_code

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.value)


class CPLStatement(object):
    def __init__(self):
        self.breaks = set()
        self.continues = set()

    def add_properties(self, stmt):
        self.breaks = self.breaks.union(stmt.breaks)
        self.continues = self.continues.union(stmt.continues)


class Program(CPLStatement):
    def __init__(self, tree):
        CPLStatement.__init__(self)
        self.add_properties(tree[1])
        self.code = tree[1].code + [QUADInstruction("", "", "", "halt", Types.INT)]
        self.errors = []
        for _break in self.breaks:
            self.errors.append(
                SemanticError(_break.line, "Invalid 'break' statement! 'break' should be inside 'while'/'switch'!")
            )

        for _continue in self.continues:
            self.errors.append(
                SemanticError(_continue.line, "Invalid 'continue' statement! 'continue' should be inside 'while'.")
            )


class SwitchStmt(CPLStatement):
    """
    Creates IR with the following template:

                condition.code
        case_1: if condition.result != 1 goto case_2
                case_1.code
                goto end_switch
        case_2: if condition.result != 1 goto default
                case_2.code
                goto end_switch
        default: default.code
        end_switch:
    """
    def __init__(self, tree):
        CPLStatement.__init__(self)
        condition = tree[2]
        caselist = tree[5]
        default_stmt = tree[8]
        if condition.type != Types.INT:
            self.errors = [SemanticError(
                line=tree[0].line,
                message="Invalid switch condition! the condition must be integer!"
            )]

        self.continues = default_stmt.continues.union(caselist.continues)
        cases = caselist.cases

        labels = {num: Label("case_%d" % num) for num in cases}
        end_label = Label("end_switch")
        default_label = Label("default")
        cases_code = []
        ordered_cases = list(cases.items())
        for i, (case_condition, stmt) in enumerate(ordered_cases):
            temp = TemporaryVariables.get_new_temporary_variable()
            cases_code.append(labels[case_condition])
            cases_code.append(QUADInstruction(temp, condition.value, case_condition, "!=", Types.INT))
            if i + 1 < len(ordered_cases):
                next_state, _ = ordered_cases[i + 1]
                cases_code.append(QUADInstruction.get_conditional_jump(temp, labels[next_state]))

            cases_code += stmt.code
            cases_code.append(QUADInstruction.get_jump(end_label))

        self.code = (condition.code + cases_code + [default_label] + default_stmt.code + [end_label])
        for _break in caselist.breaks.union(default_stmt.breaks):
            _break.label = end_label


class Caselist(CPLStatement):
    def __init__(self, tree, symbol_table):
        CPLStatement.__init__(self)
        self.cases = {}
        if isinstance(tree[0], Caselist):
            caselist = tree[0]
            self.add_properties(caselist)
            self.add_properties(tree[4])
            num = Factor([tree[2]], symbol_table)
            if num.type != Types.INT:
                self.errors = [
                    SemanticError(line=tree[1].line, message="switch case type must be integer!")
                ]

            self.cases.update(caselist.cases)
            if num.value in self.cases:
                e = SemanticError(
                    line=tree[1].line,
                    message="Duplicate cases (%d) in the same switch!" % num.value
                )
                if hasattr(self, "errors"):
                    self.errors.append(e)
                else:
                    self.errors = [e]

            self.cases[num.value] = tree[4]
            self.code = caselist.code + tree[4].code
        else:
            self.code = []


class WhileStmt(CPLStatement):
    def __init__(self, tree):
        CPLStatement.__init__(self)
        condition_label = Label("condition")
        end_while_label = Label("end_while")
        condition = tree[2]
        self.code = (
                [condition_label] +
                condition.code +
                [QUADInstruction.get_conditional_jump(condition.value, end_while_label)] +
                tree[4].code +
                [QUADInstruction.get_jump(condition_label), end_while_label]
        )

        for _break in tree[4].breaks:
            _break.label = end_while_label

        for _continue in tree[4].continues:
            _continue.label = condition_label


class StmtList(CPLStatement):
    def __init__(self, tree):
        CPLStatement.__init__(self)
        if isinstance(tree[0], StmtList):
            self.add_properties(tree[0])
            self.add_properties(tree[1])
            self.code = tree[0].code + tree[1].code
        else:
            self.code = []


class StmtBlock(CPLStatement):
    def __init__(self, tree):
        CPLStatement.__init__(self)
        self.add_properties(tree[1])
        self.code = tree[1].code


class ContinueStmt(CPLStatement):
    def __init__(self, tree):
        CPLStatement.__init__(self)
        self.label = None
        self.line = tree[0].line
        self.continues.add(self)

    @property
    def code(self):
        if self.label:
            return [QUADInstruction.get_jump(self.label)]
        else:
            return [self]


class BreakStmt(CPLStatement):
    def __init__(self, tree):
        CPLStatement.__init__(self)
        self.label = None
        self.line = tree[0].line
        self.breaks.add(self)

    @property
    def code(self):
        if self.label:
            return [QUADInstruction.get_jump(self.label)]
        else:
            return [self]


class Stmt(CPLStatement):
    def __init__(self, tree):
        CPLStatement.__init__(self)
        self.code = tree[0].code
        self.add_properties(tree[0])


class IfStmt(CPLStatement):
    def __init__(self, tree):
        CPLStatement.__init__(self)
        boolexpr = tree[2]
        true_stmt = tree[4]
        false_stmt = tree[6]
        self.add_properties(true_stmt)
        self.add_properties(false_stmt)
        else_label = Label("else")
        end_if_label = Label("endif")
        self.code = (
                boolexpr.code +
                [QUADInstruction.get_conditional_jump(boolexpr.value, else_label)] +
                true_stmt.code +
                [QUADInstruction.get_jump(end_if_label), else_label] +
                false_stmt.code +
                [end_if_label]
        )


class CastStmt(CPLObject, CPLStatement):
    NODE_TYPE = "cast_stmt"

    def __init__(self, tree, symbol_table):
        CPLStatement.__init__(self)
        id = Factor(tree, symbol_table)
        self.type = tree[4]
        expression = tree[7]
        self.value = id.value
        if id.type == Types.INT and self.type == Types.FLOAT:
            self.errors = [
                SemanticError(line=tree[1].line, message="Invalid static_cast! can't assign float to int!")
            ]

        self.code = expression.code
        if expression.type == Types.INT and self.type == Types.FLOAT:
            self.code.append(QUADInstruction(self.value, expression.value, "", "CAST_TO_REAL", Types.INT))
        elif expression.type == Types.FLOAT and self.type == Types.INT:
            self.code.append(QUADInstruction(self.value, expression.value, "", "CAST_TO_INT", Types.FLOAT))
        else:
            self.code.append(QUADInstruction(self.value, expression.value, "", "=", self.type))


class AssignmentStmt(CPLObject, CPLStatement):
    NODE_TYPE = "AssignmentStmt"

    def __init__(self, tree, symbol_table):
        CPLStatement.__init__(self)
        left = Factor(tree, symbol_table)
        right = tree[2]
        if left.type == Types.INT and right.type == Types.FLOAT:
            self.errors = [
                SemanticError(line=tree[1].line, message="Invalid assignment! can't assign float to int!")
            ]

        self.type = Types.FLOAT if Types.FLOAT in (right.type, left.type) else Types.INT
        self.value = left.value
        self.code = right.code + [QUADInstruction(self.value, right.value, "", "=", self.type)]


class OutputStatement(CPLObject, CPLStatement):
    NODE_TYPE = "output_stmt"

    def __init__(self, tree):
        CPLStatement.__init__(self)
        self.copy_properties_of_node(tree, index=2)
        self.code.append(QUADInstruction(self.value, "", "", "WRITE", self.type))


class InputStatement(CPLObject, CPLStatement):
    NODE_TYPE = "input_stmt"

    def __init__(self, tree, symbol_table):
        CPLStatement.__init__(self)
        tree[2] = Factor([tree[2]], symbol_table)
        self.copy_properties_of_node(tree, index=2)
        self.code = [QUADInstruction(self.value, "", "", "READ", self.type)]


class BoolExpr(CPLObject):
    NODE_TYPE = "boolexpr"

    def __init__(self, tree):
        if self.get_subtree_node_type(tree) == BoolTerm.NODE_TYPE:
            self.copy_properties_of_node(tree)
        else:
            self.handle_or(tree)

    def handle_or(self, subtree):
        left = subtree[0]
        right = subtree[2]
        self.handle_binary_operation_default_values(subtree)
        self.code += QUADInstruction.get_or(self.value, left.value, right.value)


class BoolTerm(CPLObject):
    NODE_TYPE = "boolterm"

    def __init__(self, tree):
        if self.get_subtree_node_type(tree) == BoolFactor.NODE_TYPE:
            self.copy_properties_of_node(tree)
        else:
            self.handle_and(tree)

    def handle_and(self, subtree):
        left = subtree[0]
        right = subtree[2]
        self.handle_binary_operation_default_values(subtree)
        self.code += [
            QUADInstruction(self.value, left.value, 1, "==", self.type),
            QUADInstruction(self.value, right.value, self.value, "==", self.type)
        ]


class BoolFactor(CPLObject):
    NODE_TYPE = "boolfactor"

    def __init__(self, tree):
        if self.get_subtree_node_type(tree) == Expression.NODE_TYPE:
            operator = tree[1].value
            if operator == ">=":
                self.handle_larger_or_equal(tree)
            elif operator == "<=":
                self.handle_smaller_or_equal(tree)
            else:
                self.handle_binary_operation(tree)
        else:
            self.handle_boolexpression(tree)

        # The result of RELOP is always INT!
        self.type = Types.INT

    def handle_boolexpression(self, tree):
        self.copy_properties_of_node(tree, index=2)
        self.code.append(QUADInstruction.get_not(self.value, self.value, self.type))

    def handle_larger_or_equal(self, subtree):
        left = subtree[0]
        right = subtree[2]
        self.handle_binary_operation_default_values(subtree)
        self.value = TemporaryVariables.get_new_temporary_variable()
        temp = TemporaryVariables.get_new_temporary_variable()
        self.code += [
            QUADInstruction(temp, left.value, right.value, "==", self.type),
            QUADInstruction(self.value, left.value, right.value, ">", self.type)
        ] + QUADInstruction.get_or(self.value, self.value, temp)

    def handle_smaller_or_equal(self, subtree):
        left = subtree[0]
        right = subtree[2]
        self.handle_binary_operation_default_values(subtree)
        self.value = TemporaryVariables.get_new_temporary_variable()
        temp = TemporaryVariables.get_new_temporary_variable()
        self.code += [
            QUADInstruction(temp, left.value, right.value, "==", self.type),
            QUADInstruction(self.value, left.value, right.value, "<", self.type)
        ] + QUADInstruction.get_or(self.value, self.value, temp)


class Expression(CPLObject):
    NODE_TYPE = "expression"

    def __init__(self, subtree):
        if self.get_subtree_node_type(subtree) == Term.NODE_TYPE:
            self.copy_properties_of_node(subtree)
        else:
            self.handle_binary_operation(subtree)


class Term(CPLObject):
    NODE_TYPE = "term"

    def __init__(self, subtree):
        if self.get_subtree_node_type(subtree) == Factor.NODE_TYPE:
            self.copy_properties_of_node(subtree)
        else:
            self.handle_binary_operation(subtree)


class Factor(CPLObject):
    NODE_TYPE = "factor"

    def __init__(self, ast_subtree, symbol_table):
        first_token = ast_subtree[0]
        if first_token.type == "NUM":
            self.handle_number(ast_subtree)
        elif first_token.type == "ID":
            self.handle_id(ast_subtree, symbol_table)
        elif first_token.type == "LEFT_PARENTHESIS":
            self.copy_properties_of_node(ast_subtree, 1)

    def handle_number(self, ast_subtree):
        self.type = self.get_num_type(ast_subtree[0].value)
        self.value = (
            float(ast_subtree[0].value) if self.type == Types.FLOAT else int(ast_subtree[0].value)
        )
        self.code = []

    def handle_id(self, ast_subtree, symbol_table):
        symbol = symbol_table.get_symbol(ast_subtree[0].value)
        if not symbol:
            self.errors = [
                SemanticError(line=ast_subtree[0].line, message="Undefined symbol: %s" % ast_subtree[0].value)
            ]
            self.type = None
            self.value = ast_subtree[0].value
            self.code = []
            return

        self.type = symbol.type
        self.value = symbol.name
        self.code = []

    @staticmethod
    def get_num_type(number):
        if type(number) == float:
            return Types.FLOAT
        else:
            return Types.INT


class QUADInstruction(object):
    QUAD_OPERATORS_TABLE = {
        ("*", Types.INT): "IMLT",
        ("*", Types.FLOAT): "RMLT",
        ("/", Types.INT): "IDIV",
        ("/", Types.FLOAT): "RDIV",
        ("+", Types.INT): "IADD",
        ("+", Types.FLOAT): "RADD",
        ("-", Types.INT): "ISUB",
        ("-", Types.FLOAT): "RSUB",
        ("==", Types.INT): "IEQL",
        ("==", Types.FLOAT): "REQL",
        ("!=", Types.INT): "INQL",
        ("!=", Types.FLOAT): "RNQL",
        (">", Types.INT): "IGRT",
        (">", Types.FLOAT): "RGRT",
        ("<", Types.INT): "ILSS",
        ("<", Types.FLOAT): "RLSS",
        ("READ", Types.INT): "IINP",
        ("READ", Types.FLOAT): "RINP",
        ("WRITE", Types.INT): "IPRT",
        ("WRITE", Types.FLOAT): "RPRT",
        ("=", Types.INT): "IASN",
        ("=", Types.FLOAT): "RASN",
        ("CAST_TO_REAL", Types.INT): "ITOR",
        ("CAST_TO_INT", Types.FLOAT): "RTOI",
        ("conditional_jump", Types.INT): "JMPZ",
        ("jump", Types.INT): "JUMP",
        ("halt", Types.INT): "HALT"
    }

    def __init__(self, dest, op1, op2, operator, type):
        self.dest, self.op1, self.op2, self.type = dest, op1, op2, type
        self.operator = operator

    @property
    def code(self):
        inst = "%s %s %s %s" % (
            self.QUAD_OPERATORS_TABLE[(self.operator, self.type)],
            self.dest,
            self.op1,
            self.op2
        )
        return inst.strip()

    @classmethod
    def get_not(cls, dest, op1, type):
        return cls(dest, op1, 1, "!=", type)

    @classmethod
    def get_or(cls, dest, op1, op2):
        return [cls(dest, op1, op2, "+", Types.INT), cls(dest, dest, 0, ">", Types.INT)]

    @classmethod
    def get_conditional_jump(cls, dest, label):
        return cls(dest, label.name, "", "conditional_jump", Types.INT)

    @classmethod
    def get_jump(cls, label):
        if label:
            return cls(label.name, "", "", "jump", Types.INT)

        return cls("UNDEF", "", "", "jump", Types.INT)


def get_ir(cpl_ast, symbol_table):
    Label.reset()
    TemporaryVariables.reset()
    transformer = CPLTransformer(symbol_table)
    ir_tree = transformer.transform(cpl_ast)
    if transformer.errors:
        raise CPLCompoundException(transformer.errors)

    ir = []
    for instruction in ir_tree.code:
        try:
            if type(instruction) in (BreakStmt, ContinueStmt):
                ir.append(instruction.code[0].code)
            else:
                ir.append(instruction.code)
        except Exception:
            ir.append(instruction.code)

    return ir


if __name__ == "__main__":
    import sys
    input_filename = sys.argv[1]
    with open(input_filename) as inf:
        ast = build_ast(CPLTokenizer(inf.read()))
        sym = SymbolTable.build_form_ast(ast)
        for i in get_ir(ast, sym):
            print("'%s', " % i)




