# File: cla.py
# Date: 8 - November - 2018
#
# Implementation of a CPL lexical analyzer.
#
# Author: Nir Moshe.
"""
cla.py usage:
    python cla.py <cpl_file>.src

This script produces a new file <cpl_file>.tok which contains list of tokens which represents the CPL language.
Every line in the *.tok file has 3 fields: the token name, the lexeme and attributes (optional).

Author: Nir Moshe.
"""

__author__ = "Nir Moshe"

from collections import namedtuple
import logging
import os
import re
import sys

Token = namedtuple("Token", ["name", "lexeme", "attribute"])
ContextToken = namedtuple("ContextToken", ["token", "line_number"])


class TokenPattern:
    def __init__(self, pattern):
        """
        This class represents a token's pattern. This is all a runtime optimization - compiling the regular expression
        once before using it multiple time. It also provide nice abstraction to the pattern matching.

        :param pattern: String which represents a regular expression.
        """
        self.pattern = re.compile(r"^({regex_pattern}).*".format(regex_pattern=pattern), re.MULTILINE)

    def match(self, string):
        """
        :param string: String to check if matching against the pattern.

        :return: If match return the lexeme otherwise, returns None.
        """
        match = self.pattern.match(string)
        if match:
            return match.group(1)

        return None


def id_handler(matching_string):
    return Token(name="ID", lexeme=matching_string, attribute=matching_string)


def int_handler(matching_string):
    return Token(name="NUM", lexeme=matching_string, attribute=int(matching_string))


def float_handler(matching_string):
    return Token(name="NUM", lexeme=matching_string, attribute=float(matching_string))


def operator_handler(matching_string):
    return Token(name="RELOP", lexeme=matching_string, attribute=matching_string)


class CPLTokenizer:
    NOP_TOKEN_NAME = "IGNORE"
    INVALID_TOKEN_NAME = "INVALID_TOKEN"

    @classmethod
    def nop_handler(cls, matching_string):
        return Token(cls.NOP_TOKEN_NAME, matching_string, "")

    @classmethod
    def invalid_token_handler(cls, matching_string):
        return Token(cls.INVALID_TOKEN_NAME, matching_string, "")

    def newline_handler(self):
        def handler(matching_string):
            self.line_number += matching_string.count("\n")
            return self.nop_handler(matching_string)

        return handler

    def __init__(self, raw_content):
        """
        :param raw_content:
        """
        self.raw_content = raw_content
        self.cursor = 0
        self.line_number = 1
        self.token_patterns = [
            # Comments - Should be non-greedy regex.
            (TokenPattern(r"/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/"), self.newline_handler()),

            # Keywords
            (TokenPattern("break"), lambda _: Token(name="BREAK", lexeme="break", attribute="")),
            (TokenPattern("case"), lambda _: Token(name="CASE", lexeme="case", attribute="")),
            (TokenPattern("continue"), lambda _: Token(name="CONTINUE", lexeme="continue", attribute="")),
            (TokenPattern("default"), lambda _: Token(name="DEFAULT", lexeme="default", attribute="")),
            (TokenPattern("else"), lambda _: Token(name="ELSE", lexeme="else", attribute="")),
            (TokenPattern("float"), lambda _: Token(name="FLOAT", lexeme="float", attribute="")),
            (TokenPattern("if"), lambda _: Token(name="IF", lexeme="if", attribute="")),
            (TokenPattern("int"), lambda _: Token(name="INT", lexeme="int", attribute="")),
            (TokenPattern("read"), lambda _: Token(name="READ", lexeme="read", attribute="")),
            (TokenPattern("static_cast"), lambda _: Token(name="STATIC_CAST", lexeme="static_cast", attribute="")),
            (TokenPattern("switch"), lambda _: Token(name="SWITCH", lexeme="switch", attribute="")),
            (TokenPattern("while"), lambda _: Token(name="WHILE", lexeme="while", attribute="")),
            (TokenPattern("write"), lambda _: Token(name="WRITE", lexeme="write", attribute="")),

            # Symbols
            (TokenPattern(r"\("), lambda _: Token(name="LEFT_PARENTHESIS", lexeme="(", attribute="")),
            (TokenPattern(r"\)"), lambda _: Token(name="RIGHT_PARENTHESIS", lexeme=")", attribute="")),
            (TokenPattern("{"), lambda _: Token(name="LEFT_CURLY_BRACKETS", lexeme="{", attribute="")),
            (TokenPattern("}"), lambda _: Token(name="RIGHT_CURLY_BRACKETS", lexeme="}", attribute="")),
            (TokenPattern(","), lambda _: Token(name="COMMA", lexeme=",", attribute="")),
            (TokenPattern(r"\."), lambda _: Token(name="POINT", lexeme=".", attribute="")),
            (TokenPattern(":"), lambda _: Token(name="COLON", lexeme=":", attribute="")),
            (TokenPattern(";"), lambda _: Token(name="SEMICOLON", lexeme=";", attribute="")),
            (TokenPattern("="), lambda _: Token(name="EQUAL_SIGN", lexeme="=", attribute="")),

            # Operators
            (TokenPattern(r"==|!=|>=|<=|<|>"), operator_handler),
            (TokenPattern(r"\+"), lambda _: Token(name="ADDOP", lexeme="+", attribute="+")),
            (TokenPattern("-"), lambda _: Token(name="ADDOP", lexeme="-", attribute="-")),
            (TokenPattern(r"\*"), lambda _: Token(name="MULOP", lexeme="*", attribute="*")),
            (TokenPattern("/"), lambda _: Token(name="MULOP", lexeme="/", attribute="/")),
            (TokenPattern(r"\|\|"), lambda _: Token(name="OR", lexeme="||", attribute="")),
            (TokenPattern("&&"), lambda _: Token(name="AND", lexeme="&&", attribute="")),
            (TokenPattern("!"), lambda _: Token(name="NOT", lexeme="!", attribute="")),

            # ID (Must start with letter, no more than 9 characters).
            (TokenPattern(r"[a-zA-Z][a-zA-Z0-9]{0,8}"), id_handler),

            # Number
            (TokenPattern(r"\d+\.\d*"), float_handler),
            (TokenPattern(r"\d+"), int_handler),

            # New line and whitespace
            (TokenPattern(r"\n"), self.newline_handler()),
            (TokenPattern(r"\s"), CPLTokenizer.nop_handler),

            # Else (or the invalid symbols)...
            (TokenPattern(r".{1}"), CPLTokenizer.invalid_token_handler),
            (TokenPattern(r"[a-zA-Z][a-zA-Z0-9]{8,}"), CPLTokenizer.invalid_token_handler),
            (TokenPattern(r"[0-9]+[a-zA-Z0-9]+"), CPLTokenizer.invalid_token_handler),
        ]
        self._tokens = self.__tokenize_first_pass()
        self._tokens_index = 0

    def __tokenize_first_pass(self):
        """
        :return: List of `ContextTokens`. The list doesn't contain whitespaces and comments.
        """
        tokens = []
        while self.cursor < len(self.raw_content):
            current_string = self.raw_content[self.cursor:]

            # First, lets check if there are any possible matches.
            possible_matches = self.__get_all_possible_matches(current_string)
            token = max(possible_matches, key=lambda _token: len(_token.lexeme))
            self.cursor += len(token.lexeme)

            # Filter whitespaces and comments...
            if token.name != CPLTokenizer.NOP_TOKEN_NAME:
                tokens.append(ContextToken(token, self.line_number))

        return tokens

    def __get_all_possible_matches(self, string):
        """
        :param string: String.

        :return: Returns list of Tokens, every token represents a possible match.
        """
        possible_matches = []
        for token_pattern, handler in self.token_patterns:
            lexeme = token_pattern.match(string)
            if lexeme is not None:
                token = handler(lexeme)
                possible_matches.append(token)

        return possible_matches

    def get_next_token(self):
        """
        :return: The next Token object.

        :raises StopIteration if there are no more tokens.
        """
        if self._tokens_index >= len(self._tokens):
            raise StopIteration()

        token, line = self._tokens[self._tokens_index]
        self._tokens_index += 1

        # This is my implementation for lookbehind with un-fixed size. (these aren't RELOP, should be considered as
        # symbols).
        if token.name == "RELOP" and token.attribute == "<" and self.__lookbehind_is_static_cast(2):
            return ContextToken(Token(name="LEFT_STATIC_CAST_BRACKETS", lexeme="<", attribute=""), line)
        elif token.name == "RELOP" and token.attribute == ">" and self.__lookbehind_is_static_cast(4):
            return ContextToken(Token(name="RIGHT_STATIC_CAST_BRACKETS", lexeme=">", attribute=""), line)

        return ContextToken(token, line)

    def __lookbehind_is_static_cast(self, number_of_tokens_to_lookbehind):
        if self._tokens_index - number_of_tokens_to_lookbehind < 0:
            return False

        return self._tokens[self._tokens_index - number_of_tokens_to_lookbehind].token.name == "STATIC_CAST"

    def __iter__(self):
        return self

    def __next__(self):
        return self.get_next_token()


def compiler_stub(cpl_string, output_stream, error_stream, signature):
    """
    The function simulates a CPL compiler.

    :param cpl_string: String which represent the CPL program.
    :param output_stream: Tokens will be written to this stream.
    :param error_stream: Errors will be written to this stream.
    :param signature:
        File signature. The signature will be written at the end of the `output_stream` and at the end of
        `error_stream`.
    """
    tokenizer = CPLTokenizer(cpl_string)
    for token, line in tokenizer:
        if token.name == CPLTokenizer.INVALID_TOKEN_NAME:
            error_stream.error("Error: Invalid token: '%s' in line %d!", str(token.lexeme), line)
        else:
            output_stream.info("\t".join([str(field) for field in token]))

    error_stream.info(signature)
    output_stream.info(signature)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    input_filename = sys.argv[1]
    input_filename_no_ext, _ = os.path.splitext(input_filename)

    with open(input_filename) as input_fd, open(input_filename_no_ext + ".tok", "w") as output_fd:
        output_file = logging.getLogger("file_output")
        output_file.addHandler(logging.StreamHandler(output_fd))
        output_file.setLevel(logging.INFO)
        stderr = logging.getLogger("stderr")
        stderr.addHandler(logging.StreamHandler(sys.stderr))
        stderr.setLevel(logging.INFO)
        compiler_stub(
            cpl_string=input_fd.read(),
            output_stream=output_file,
            error_stream=stderr,
            signature="Nir Moshe, 300307824. Compilation Theory."
        )
