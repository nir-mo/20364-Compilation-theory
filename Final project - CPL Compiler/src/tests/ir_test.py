# Author: Nir Moshe.
# Date: 31-Jan-2019

from unittest import main, TestCase
import sys
sys.path.append("..")

from lark import Tree

from cla import CPLTokenizer
from cpl_ast import build_ast
from ir import CPLTransformer, TemporaryVariables, Label, get_ir, SemanticError
from symbol_table import SymbolTable, Types


class FakeToken:
    def __init__(self, type, value, line=0):
        self.type, self.value, self.line = type, value, line


class QuadTransformerTest(TestCase):
    def setUp(self):
        TemporaryVariables.reset()
        Label.reset()
        symbol_table = SymbolTable()
        symbol_table.add_symbol("a_int", Types.INT, 1)
        symbol_table.add_symbol("b_int", Types.INT, 1)
        symbol_table.add_symbol("c_float", Types.FLOAT, 2)
        symbol_table.add_symbol("d_float", Types.FLOAT, 2)
        self.transformer = CPLTransformer(symbol_table)

    def test_id_factor(self):
        int_result = self.transformer.transform(Tree("factor", [FakeToken("ID", "a_int")]))
        self.assertEqual("a_int", int_result.value)
        self.assertEqual(Types.INT, int_result.type)
        self.assertEqual([], int_result.code)

        float_result = self.transformer.transform(Tree("factor", [FakeToken("ID", "c_float")]))
        self.assertEqual("c_float", float_result.value)
        self.assertEqual(Types.FLOAT, float_result.type)
        self.assertEqual([], float_result.code)

    def test_num_factor(self):
        int_result = self.transformer.transform(Tree("factor", [FakeToken("NUM", 7)]))
        self.assertEqual(7, int_result.value)
        self.assertEqual(Types.INT, int_result.type)
        self.assertEqual([], int_result.code)

        float_result = self.transformer.transform(Tree("factor", [FakeToken("NUM", 7.7)]))
        self.assertEqual(7.7, float_result.value)
        self.assertEqual(Types.FLOAT, float_result.type)
        self.assertEqual([], float_result.code)

    def test_expression_factor(self):
        tree = Tree("factor", [
            FakeToken("LEFT_PARENTHESIS", ""),
            Tree("expression", [
                Tree("term", [
                    Tree("factor", [FakeToken("NUM", 5)])
                ])
            ]),
            FakeToken(")", "")]
        )
        int_result = self.transformer.transform(tree)
        self.assertEqual(5, int_result.value)
        self.assertEqual(Types.INT, int_result.type)
        self.assertEqual([], int_result.code)

    def test_simple_term(self):
        # equivalent to: 3 * a_int
        tree = Tree("term", [
            Tree("term", [
                Tree("factor", [FakeToken("NUM", 3)])
            ]),
            FakeToken("MULOP", "*"),
            Tree("factor", [FakeToken("ID", "a_int")])
        ])
        int_result = self.transformer.transform(tree)
        self.assertEqual("t1", int_result.value)
        self.assertEqual(Types.INT, int_result.type)
        code = [inst.code for inst in int_result.code]
        self.assertEqual(["IMLT t1 3 a_int"], code)

    def test_different_types_term(self):
        # equivalent to: 3.3 * a_int
        tree = Tree("term", [
            Tree("term", [
                Tree("factor", [FakeToken("NUM", 3.3)])
            ]),
            FakeToken("MULOP", "/"),
            Tree("factor", [FakeToken("ID", "a_int")])
        ])
        int_result = self.transformer.transform(tree)
        self.assertEqual("t1", int_result.value)
        self.assertEqual(Types.FLOAT, int_result.type)
        code = [inst.code for inst in int_result.code]
        self.assertEqual(['ITOR t2 a_int', 'RDIV t1 3.3 t2'], code)

    def test_expression(self):
        # equivalent to: 3.3 * (5 + a_int)
        tree = Tree("expression",
            [
                Tree("term",
                     [
                         Tree("term", [Tree("factor", [FakeToken("NUM", 3.3)])]),
                         FakeToken("MULOP", '*'),
                         Tree("factor",
                              [
                                  FakeToken("LEFT_PARENTHESIS", ''),
                                  Tree("expression",
                                       [
                                           Tree("expression",
                                                [Tree("term", [Tree("factor", [FakeToken("NUM", 5)])])]
                                            ),
                                           FakeToken("ADDOP", '+'),
                                           Tree("term", [Tree("factor", [FakeToken("ID", 'a_int')])])
                                       ]
                                    )
                               ]
                         )
                     ]
                )
            ]
        )
        float_result = self.transformer.transform(tree)
        self.assertEqual("t2", float_result.value)
        self.assertEqual(Types.FLOAT, float_result.type)
        code = [inst.code for inst in float_result.code]
        self.assertEqual(
            ['IADD t1 5 a_int', 'ITOR t3 t1', 'RMLT t2 3.3 t3'],
            code
        )

    def test_boolexpr(self):
        # Test expressions with the pattern: !(a_int RELOP c_float)
        operators_to_instructions = {
            ">": ['ITOR t2 a_int', 'RGRT t1 t2 c_float', 'INQL t1 t1 1'],
            "<": ['ITOR t2 a_int', 'RLSS t1 t2 c_float', 'INQL t1 t1 1'],
            "==": ['ITOR t2 a_int', 'REQL t1 t2 c_float', 'INQL t1 t1 1'],
            "!=": ['ITOR t2 a_int', 'RNQL t1 t2 c_float', 'INQL t1 t1 1'],
            ">=": [
                'ITOR t2 a_int',
                'REQL t4 t2 c_float',
                'RGRT t3 t2 c_float',
                'IADD t3 t3 t4',
                'IGRT t3 t3 0',
                'INQL t3 t3 1'
            ],
            "<=": [
                'ITOR t2 a_int',
                'REQL t4 t2 c_float',
                'RLSS t3 t2 c_float',
                'IADD t3 t3 t4',
                'IGRT t3 t3 0',
                'INQL t3 t3 1'
            ],
        }
        for operator, instructions in operators_to_instructions.items():
            TemporaryVariables.reset()
            tree = Tree("boolexpr", [
                Tree("boolterm", [
                    Tree("boolfactor", [
                        FakeToken("NOT", ''),
                        FakeToken("LEFT_PARENTHESIS", ''),
                        Tree("boolexpr", [
                            Tree("boolterm", [
                                Tree("boolfactor", [
                                    Tree("expression", [
                                        Tree("term", [
                                            Tree("factor", [FakeToken("ID", 'a_int')])
                                        ])
                                    ]),
                                    FakeToken("RELOP", operator),
                                    Tree("expression", [
                                        Tree("term", [
                                            Tree("factor", [FakeToken("ID", 'c_float')])
                                        ])
                                    ])
                                ])
                            ])
                        ])
                    ])
                ])
            ])
            int_result = self.transformer.transform(tree)
            self.assertEqual(Types.INT, int_result.type)
            code = [inst.code for inst in int_result.code]
            self.assertEqual(instructions, code)

    def test_assignment(self):
        tree = Tree("assignment_stmt", [
            FakeToken("ID", 'c_float'),
            FakeToken("EQUAL_SIGN", ''),
            Tree("expression", [
                Tree("term", [
                    Tree("factor", [FakeToken("ID", 'b_int')])
                ])
            ])
        ])
        result = self.transformer.transform(tree)
        self.assertEqual("c_float", result.value)
        self.assertEqual(Types.FLOAT, result.type)
        code = [inst.code for inst in result.code]
        self.assertEqual(['RASN c_float b_int'], code)

    def test_illegal_assignment(self):
        tree = Tree("assignment_stmt", [
            FakeToken("ID", 'a_int'),
            FakeToken("EQUAL_SIGN", ''),
            Tree("expression", [
                Tree("term", [
                    Tree("factor", [FakeToken("ID", 'c_float')])
                ])
            ])
        ])
        self.transformer.transform(tree)
        self.assertIsInstance(self.transformer.errors[0], SemanticError)

    def test_input_stmt(self):
        tree = Tree("input_stmt", [
            FakeToken("READ", ""),
            FakeToken("LEFT_PARENTHESIS", ''),
            FakeToken("ID", 'a_int'),
            FakeToken("RIGHT_PARENTHESIS", ''),
        ])
        result = self.transformer.transform(tree)
        self.assertEqual("a_int", result.value)
        self.assertEqual(Types.INT, result.type)
        code = [inst.code.strip() for inst in result.code]
        self.assertEqual(['IINP a_int'], code)

    def test_static_cast(self):
        tree = Tree("cast_stmt", [
            FakeToken("ID", 'a_int'),
            FakeToken("EQUAL_SIGN", ''),
            FakeToken("STATIC_CAST", ''),
            FakeToken("LEFT_STATIC_CAST_BRACKETS", ''),
            Tree("type", [FakeToken("INT", '')]),
            FakeToken("RIGHT_STATIC_CAST_BRACKETS", ''),
            FakeToken("LEFT_PARENTHESIS", ''),
            Tree("expression", [
                Tree("term", [
                    Tree("factor", [FakeToken("NUM", 3.33)])
                ])
            ])
        ])
        result = self.transformer.transform(tree)
        self.assertEqual("a_int", result.value)
        self.assertEqual(Types.INT, result.type)
        code = [inst.code for inst in result.code]
        self.assertEqual(['RTOI a_int 3.33'], code)

    def test_static_cast_same_type(self):
        tree = Tree("cast_stmt", [
            FakeToken("ID", 'a_int'),
            FakeToken("EQUAL_SIGN", ''),
            FakeToken("STATIC_CAST", ''),
            FakeToken("LEFT_STATIC_CAST_BRACKETS", ''),
            Tree("type", [FakeToken("INT", '')]),
            FakeToken("RIGHT_STATIC_CAST_BRACKETS", ''),
            FakeToken("LEFT_PARENTHESIS", ''),
            Tree("expression", [
                Tree("term", [
                    Tree("factor", [FakeToken("ID", "b_int")])
                ])
            ])
        ])
        result = self.transformer.transform(tree)
        self.assertEqual("a_int", result.value)
        self.assertEqual(Types.INT, result.type)
        code = [inst.code for inst in result.code]
        self.assertEqual(['IASN a_int b_int'], code)

    def test_invalid_cast(self):
        # test: int a = static_cast<float>(3.33)
        tree = Tree("cast_stmt", [
            FakeToken("ID", 'a_int'),
            FakeToken("EQUAL_SIGN", ''),
            FakeToken("STATIC_CAST", ''),
            FakeToken("LEFT_STATIC_CAST_BRACKETS", ''),
            Tree("type", [FakeToken("FLOAT", '')]),
            FakeToken("RIGHT_STATIC_CAST_BRACKETS", ''),
            FakeToken("LEFT_PARENTHESIS", ''),
            Tree("expression", [
                Tree("term", [
                    Tree("factor", [FakeToken("NUM", 3.33)])
                ])
            ])
        ])
        self.transformer.transform(tree)
        self.assertIsInstance(self.transformer.errors[0], SemanticError)

    def test_if(self):
        tree = Tree("if_stmt", [
            FakeToken("IF", ''),
            FakeToken("LEFT_PARENTHESIS", ''),
            Tree("boolexpr", [
                Tree("boolterm", [
                    Tree("boolfactor", [
                        Tree("expression", [
                            Tree("term", [Tree("factor", [FakeToken("ID", 'a_int')])])
                        ]),
                        FakeToken("RELOP", '<'),
                        Tree("expression", [
                            Tree("term", [
                                Tree("factor", [FakeToken("ID", 'b_int')])
                            ])
                        ])
                    ])
                ])
            ]),
            FakeToken("RIGHT_PARENTHESIS", ''),
            Tree("stmt", [
                Tree("output_stmt", [
                    FakeToken("WRITE", ''),
                    FakeToken("LEFT_PARENTHESIS", ''),
                    Tree("expression", [
                        Tree("term", [
                            Tree("factor", [FakeToken("ID", 'a_int')])
                        ])
                    ]),
                    FakeToken("RIGHT_PARENTHESIS", ''),
                    FakeToken("SEMICOLON", '')
                ])]),
            FakeToken("ELSE", ''),
            Tree("stmt", [
                Tree("output_stmt", [
                    FakeToken("WRITE", ''),
                    FakeToken("LEFT_PARENTHESIS", ''),
                    Tree("expression", [
                        Tree("term", [Tree("factor", [FakeToken("ID", 'b_int')])])
                    ]),
                    FakeToken("RIGHT_PARENTHESIS", ''),
                    FakeToken("SEMICOLON", '')
                ])
            ])
        ])
        result = self.transformer.transform(tree)
        code = [inst.code for inst in result.code]
        self.assertEqual([
            'ILSS t1 a_int b_int',
            'JMPZ else_label_0 t1',
            'IPRT a_int',
            'JUMP endif_label_1',
            'else_label_0:',
            'IPRT b_int',
            'endif_label_1:'
        ], code)

    def test_switch(self):
        cpl_program = """
        a, b: int;
        {
            switch(a) {
                case 1: {
                    write(1);
                    break;
                }
                case 2: write(2);
                case 3: {
                    switch(b) {
                        case 5: write(5);
                        default: break;
                    }
                }
                case 4: write(4);
                default: write(0);
            }
        }
        """
        ast = build_ast(CPLTokenizer(cpl_program))
        sym = SymbolTable.build_form_ast(ast)
        code = [i.code for i in get_ir(ast, sym)]
        self.assertEqual(code, [
            'case_1_label_3:',
            'IEQL t2 a 1',
            'JMPZ case_2_label_4 t2',
            'IPRT 1',
            'JUMP end_switch_label_7',
            'JUMP end_switch_label_7',
            'case_2_label_4:',
            'IEQL t3 a 2',
            'JMPZ case_3_label_5 t3',
            'IPRT 2',
            'JUMP end_switch_label_7',
            'case_3_label_5:',
            'IEQL t4 a 3',
            'JMPZ case_4_label_6 t4',
            'case_5_label_0:',
            'IEQL t1 b 5',
            'JMPZ default_label_2 t1',
            'IPRT 5',
            'JUMP end_switch_label_1',
            'default_label_2:',
            'JUMP end_switch_label_1',
            'end_switch_label_1:',
            'JUMP end_switch_label_7',
            'case_4_label_6:',
            'IEQL t5 a 4',
            'JMPZ default_label_8 t5',
            'IPRT 4',
            'JUMP end_switch_label_7',
            'default_label_8:',
            'IPRT 0',
            'end_switch_label_7:',
            'HALT'
        ])

    def test_while(self):
        cpl_program = """
        a, b: float;
        {
            while (a < b) {
                if (b  > 100)
                    break;
                else {
                    a = a + 1;
                    continue;
                }
            }
        }
        """
        ast = build_ast(CPLTokenizer(cpl_program))
        sym = SymbolTable.build_form_ast(ast)
        code = [i.code for i in get_ir(ast, sym)]
        self.assertEqual(code, [
            'condition_label_2:',
            'RLSS t1 a b',
            'JMPZ end_while_label_3 t1',
            'ITOR t3 100',
            'RGRT t2 b t3',
            'JMPZ else_label_0 t2',
            'JUMP end_while_label_3',
            'JUMP endif_label_1',
            'else_label_0:',
            'ITOR t5 1',
            'RADD t4 a t5',
            'RASN a t4',
            'JUMP condition_label_2',
            'endif_label_1:',
            'JUMP condition_label_2',
            'end_while_label_3:',
            'HALT'
        ])


if __name__ == "__main__":
    main()
