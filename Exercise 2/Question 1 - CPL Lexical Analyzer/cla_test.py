# File: cla_test.py
# Date: 8 - November - 2018
#
# Testing the implementation of a CPL lexical analyzer.
#
# Author: Nir Moshe.

__author__ = "Nir Moshe"

import unittest
from cla import Token, CPLTokenizer, ContextToken


def get_tokens(tokenizer):
    return [token for token, _ in tokenizer]


class CLATest(unittest.TestCase):
    def test_simple_cpl(self):
        tokenizer = CPLTokenizer("    int main() { int;}")
        self.assertEqual(
            [
                Token(name='INT', lexeme='int', attribute=''),
                Token(name='ID', lexeme='main', attribute='main'),
                Token(name='LEFT_PARENTHESIS', lexeme='(', attribute=''),
                Token(name='RIGHT_PARENTHESIS', lexeme=')', attribute=''),
                Token(name='LEFT_CURLY_BRACKETS', lexeme='{', attribute=''),
                Token(name='INT', lexeme='int', attribute=''),
                Token(name='SEMICOLON', lexeme=';', attribute=''),
                Token(name='RIGHT_CURLY_BRACKETS', lexeme='}', attribute=''),
            ],
            get_tokens(tokenizer)
        )

    def test_comments(self):
        tokenizer = CPLTokenizer("""
            /**
             *
             *
             
             *  This is a comments test...
             *
             
             
             */ 
            int main() { int nir1 = 7777;
                
                /* This isn't a key word */
                int break1 = 8.8;
                float number = 3., 3.14; /* comment */
                /*
                
                    This is the end of the test!
                    */
            }
        """)
        self.assertEqual(
            [
                Token(name='INT', lexeme='int', attribute=''),
                Token(name='ID', lexeme='main', attribute='main'),
                Token(name='LEFT_PARENTHESIS', lexeme='(', attribute=''),
                Token(name='RIGHT_PARENTHESIS', lexeme=')', attribute=''),
                Token(name='LEFT_CURLY_BRACKETS', lexeme='{', attribute=''),
                Token(name='INT', lexeme='int', attribute=''),
                Token(name='ID', lexeme='nir1', attribute='nir1'),
                Token(name='EQUAL_SIGN', lexeme='=', attribute=''),
                Token(name='NUM', lexeme='7777', attribute=7777),
                Token(name='SEMICOLON', lexeme=';', attribute=''),
                Token(name='INT', lexeme='int', attribute=''),
                Token(name='ID', lexeme='break1', attribute='break1'),
                Token(name='EQUAL_SIGN', lexeme='=', attribute=''),
                Token(name='NUM', lexeme='8.8', attribute=8.8),
                Token(name='SEMICOLON', lexeme=';', attribute=''),
                Token(name='FLOAT', lexeme='float', attribute=''),
                Token(name='ID', lexeme='number', attribute='number'),
                Token(name='EQUAL_SIGN', lexeme='=', attribute=''),
                Token(name='NUM', lexeme='3.', attribute=3.0),
                Token(name='COMMA', lexeme=',', attribute=''),
                Token(name='NUM', lexeme='3.14', attribute=3.14),
                Token(name='SEMICOLON', lexeme=';', attribute=''),
                Token(name='RIGHT_CURLY_BRACKETS', lexeme='}', attribute=''),
            ],
            get_tokens(tokenizer)
        )

    def test_static_cast(self):
        tokenizer = CPLTokenizer("""
        x < 3;
        float x = static_cast  < int  
            >( y );
        """)
        self.assertEqual(
            [
                Token(name='ID', lexeme='x', attribute='x'),
                Token(name='RELOP', lexeme='<', attribute='<'),
                Token(name='NUM', lexeme='3', attribute=3),
                Token(name='SEMICOLON', lexeme=';', attribute=''),
                Token(name='FLOAT', lexeme='float', attribute=''),
                Token(name='ID', lexeme='x', attribute='x'),
                Token(name='EQUAL_SIGN', lexeme='=', attribute=''),
                Token(name='STATIC_CAST', lexeme='static_cast', attribute=''),
                Token(name='LEFT_STATIC_CAST_BRACKETS', lexeme='<', attribute=''),
                Token(name='INT', lexeme='int', attribute=''),
                Token(name='RIGHT_STATIC_CAST_BRACKETS', lexeme='>', attribute=''),
                Token(name='LEFT_PARENTHESIS', lexeme='(', attribute=''),
                Token(name='ID', lexeme='y', attribute='y'),
                Token(name='RIGHT_PARENTHESIS', lexeme=')', attribute=''),
                Token(name='SEMICOLON', lexeme=';', attribute=''),
            ],
            get_tokens(tokenizer)
        )

    def test_relop(self):
        tokenizer = CPLTokenizer("== != < > >= <=")
        self.assertEqual(
            [
                Token(name='RELOP', lexeme='==', attribute='=='),
                Token(name='RELOP', lexeme='!=', attribute='!='),
                Token(name='RELOP', lexeme='<', attribute='<'),
                Token(name='RELOP', lexeme='>', attribute='>'),
                Token(name='RELOP', lexeme='>=', attribute='>='),
                Token(name='RELOP', lexeme='<=', attribute='<='),
            ],
            get_tokens(tokenizer)
        )

    def test_operators(self):
        tokenizer = CPLTokenizer("+ - * / || && !")
        self.assertEqual(
            [
                Token(name='ADDOP', lexeme='+', attribute='+'),
                Token(name='ADDOP', lexeme='-', attribute='-'),
                Token(name='MULOP', lexeme='*', attribute='*'),
                Token(name='MULOP', lexeme='/', attribute='/'),
                Token(name='OR', lexeme='||', attribute=''),
                Token(name='AND', lexeme='&&', attribute=''),
                Token(name='NOT', lexeme='!', attribute=''),
            ],
            get_tokens(tokenizer)
        )

    def test_symbols(self):
        tokenizer = CPLTokenizer("( ) { } , : ; = < >")
        self.assertEqual(
            [
                Token(name='LEFT_PARENTHESIS', lexeme='(', attribute=''),
                Token(name='RIGHT_PARENTHESIS', lexeme=')', attribute=''),
                Token(name='LEFT_CURLY_BRACKETS', lexeme='{', attribute=''),
                Token(name='RIGHT_CURLY_BRACKETS', lexeme='}', attribute=''),
                Token(name='COMMA', lexeme=',', attribute=''),
                Token(name='COLON', lexeme=':', attribute=''),
                Token(name='SEMICOLON', lexeme=';', attribute=''),
                Token(name='EQUAL_SIGN', lexeme='=', attribute=''),
                Token(name='RELOP', lexeme='<', attribute='<'),
                Token(name='RELOP', lexeme='>', attribute='>'),
            ],
            get_tokens(tokenizer)
        )

    def test_id(self):
        for i in range(1, 10):
            tokenizer = CPLTokenizer("a" * i)
            self.assertEqual(
                [Token(name='ID', lexeme='a' * i, attribute='a' * i)],
                get_tokens(tokenizer)
            )

        tokenizer = CPLTokenizer("a" * 10)
        self.assertEqual(
            [Token(name='INVALID_TOKEN', lexeme='a' * 10, attribute='')],
            get_tokens(tokenizer)
        )

        tokenizer = CPLTokenizer("aa11a")
        self.assertEqual(
            [Token(name='ID', lexeme='aa11a', attribute='aa11a')],
            get_tokens(tokenizer)
        )

        tokenizer = CPLTokenizer("100ff0x")
        self.assertEqual(
            [Token(name='INVALID_TOKEN', lexeme='100ff0x', attribute='')],
            get_tokens(tokenizer)
        )

    def test_num(self):
        tokenizer = CPLTokenizer("9999999999 10. 3.14 0.")
        self.assertEqual(
            [
                Token(name='NUM', lexeme='9999999999', attribute=9999999999),
                Token(name='NUM', lexeme='10.', attribute=10.0),
                Token(name='NUM', lexeme='3.14', attribute=3.14),
                Token(name='NUM', lexeme='0.', attribute=0.0),
            ],
            get_tokens(tokenizer)
        )

    def test_lines_numbering(self):
        tokenizer = CPLTokenizer("""
            /**
             *
             *

             *  This is a comments test...
             *


             */ 
            int main() { int nir1 = 7777;

                /* This isn't a key word */
                int break1 = 8.8;
                float number = 3., 3.14; /* comment */
                /*

                    This is the end of the test!
                    */
            }
        """)
        self.assertEqual(
            [
                ContextToken(token=Token(name='INT', lexeme='int', attribute=''), line_number=11),
                ContextToken(token=Token(name='ID', lexeme='main', attribute='main'), line_number=11),
                ContextToken(token=Token(name='LEFT_PARENTHESIS', lexeme='(', attribute=''), line_number=11),
                ContextToken(token=Token(name='RIGHT_PARENTHESIS', lexeme=')', attribute=''), line_number=11),
                ContextToken(token=Token(name='LEFT_CURLY_BRACKETS', lexeme='{', attribute=''), line_number=11),
                ContextToken(token=Token(name='INT', lexeme='int', attribute=''), line_number=11),
                ContextToken(token=Token(name='ID', lexeme='nir1', attribute='nir1'), line_number=11),
                ContextToken(token=Token(name='EQUAL_SIGN', lexeme='=', attribute=''), line_number=11),
                ContextToken(token=Token(name='NUM', lexeme='7777', attribute=7777), line_number=11),
                ContextToken(token=Token(name='SEMICOLON', lexeme=';', attribute=''), line_number=11),
                ContextToken(token=Token(name='INT', lexeme='int', attribute=''), line_number=14),
                ContextToken(token=Token(name='ID', lexeme='break1', attribute='break1'), line_number=14),
                ContextToken(token=Token(name='EQUAL_SIGN', lexeme='=', attribute=''), line_number=14),
                ContextToken(token=Token(name='NUM', lexeme='8.8', attribute=8.8), line_number=14),
                ContextToken(token=Token(name='SEMICOLON', lexeme=';', attribute=''), line_number=14),
                ContextToken(token=Token(name='FLOAT', lexeme='float', attribute=''), line_number=15),
                ContextToken(token=Token(name='ID', lexeme='number', attribute='number'), line_number=15),
                ContextToken(token=Token(name='EQUAL_SIGN', lexeme='=', attribute=''), line_number=15),
                ContextToken(token=Token(name='NUM', lexeme='3.', attribute=3.0), line_number=15),
                ContextToken(token=Token(name='COMMA', lexeme=',', attribute=''), line_number=15),
                ContextToken(token=Token(name='NUM', lexeme='3.14', attribute=3.14), line_number=15),
                ContextToken(token=Token(name='SEMICOLON', lexeme=';', attribute=''), line_number=15),
                ContextToken(token=Token(name='RIGHT_CURLY_BRACKETS', lexeme='}', attribute=''), line_number=20),
            ],
            [token for token in tokenizer]
        )


if __name__ == "__main__":
    unittest.main()
