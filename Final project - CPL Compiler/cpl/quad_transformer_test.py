from collections import namedtuple
from unittest import main, TestCase

from lark import Tree

from symbol_table import SymbolTable, Symbol, Types
from quad_transformer import CPLTransformer, TemporaryVariables

FakeToken = namedtuple("FakeToken", ["type", "value"])


class QuadTransformerTest(TestCase):
    def setUp(self):
        TemporaryVariables.reset()
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
            ">": ['ITOR t2 a_int', 'RGRT t1 t2 c_float', 'RNQL t1 t1 1'],
            "<": ['ITOR t2 a_int', 'RLSS t1 t2 c_float', 'RNQL t1 t1 1'],
            "==": ['ITOR t2 a_int', 'REQL t1 t2 c_float', 'RNQL t1 t1 1'],
            "!=": ['ITOR t2 a_int', 'RNQL t1 t2 c_float', 'RNQL t1 t1 1'],
            ">=": [
                'ITOR t2 a_int',
                'REQL t4 t2 c_float',
                'RGRT t3 t2 c_float',
                'RADD t3 t3 t4',
                'RGRT t3 t3 0',
                'RNQL t3 t3 1'
            ],
            "<=": [
                'ITOR t2 a_int',
                'REQL t4 t2 c_float',
                'RLSS t3 t2 c_float',
                'RADD t3 t3 t4',
                'RGRT t3 t3 0',
                'RNQL t3 t3 1'
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
            float_result = self.transformer.transform(tree)
            self.assertEqual(Types.FLOAT, float_result.type)
            code = [inst.code for inst in float_result.code]
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
        with self.assertRaises(Exception):
            self.transformer.transform(tree)

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
        with self.assertRaises(ValueError):
            self.transformer.transform(tree)


if __name__ == "__main__":
    main()
