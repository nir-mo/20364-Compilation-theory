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
        self.assertEqual(["RDIV t1 3.3 a_int"], code)

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
            ['IADD t1 5 a_int', 'RMLT t2 3.3 t1'],
            code
        )


if __name__ == "__main__":
    main()
