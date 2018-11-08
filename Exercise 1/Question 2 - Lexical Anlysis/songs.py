# File: songs.py
# Date: 23 - October - 2018
#
# Implementation of a basic lexical analyzer. This lexer should analyze songs playlist.
#
# Author: Nir Moshe.

__author__ = "Nir Moshe"

import re
import sys


class Token:
    """
    Represents a token with attribute and position in the text.
    """
    INVALID_TOKEN_NAME = "UNKNOWN"

    def __init__(self, name, lexeme, attribute, line, column):
        self.name = name
        self.lexeme = lexeme
        self.attribute = attribute
        self.line = line
        self.column = column

    def is_invalid_token(self):
        """
        :return: True iff this is an invalid token, False otherwise.
        """
        return self.name == Token.INVALID_TOKEN_NAME

    def __eq__(self, other):
        if isinstance(other, Token):
            return (
                (self.name, self.lexeme, self.attribute, self.line, self.column)
                == (other.name, other.lexeme, other.attribute, other.line, other.column)
            )

        return False

    @classmethod
    def create_invalid_token(cls, lexeme, line, column):
        return cls(cls.INVALID_TOKEN_NAME, lexeme, "", line, column)


class TokenPattern:
    def __init__(self, pattern):
        """
        This class represents a token's pattern. This is all a runtime optimization - compiling the regular expression
        once before using it multiple time. It also provide nice abstraction to the pattern matching.

        :param pattern: String which represents a regular expression.
        """
        self.pattern = re.compile(r"^({regex_pattern}).*".format(regex_pattern=pattern))

    def match(self, string):
        """
        :param string: String to check if matching against the pattern.

        :return: If match return the lexeme otherwise, returns None.
        """
        match = self.pattern.match(string)
        if match:
            return match.group(1)

        return None


def default_handler(token_name):
    def _handler(lexeme, line, column):
        return Token(token_name, lexeme, "", line, column)

    return _handler


def number_handler(lexeme, line, column):
    return Token("NUMBER", lexeme, int(lexeme), line, column)


def quoted_string_handler(lexeme, line, column):
    return Token("QUOTED_STRING", lexeme, lexeme[1:-1], line, column)


# This list defines all the tokens in out language. It holds pairs of `TokenPattern` and handler function.
DEFAULT_TOKEN_PATTERNS = [
    (TokenPattern(r"\[playlist\]"), default_handler("PLAYLIST")),
    (TokenPattern(r"\[song\]"), default_handler("SONG")),
    (TokenPattern(r"\[length\]"), default_handler("LENGTH")),
    (TokenPattern(r"\[artist\]"), default_handler("ARTIST")),

    # Should be non-greedy. Quoted strings may contain white spaces (unlike other strings).
    (TokenPattern(r'"[\S \t]*?"'), quoted_string_handler),
    (TokenPattern(r"\d+"), number_handler),
    (TokenPattern(r"\d+:[0-5]{1}\d{1}"), default_handler("DURATION")),

    # Any word character (letter, number, underscore) + any of the characters: ! # - & '.
    (TokenPattern(r"[\w&-'!#]+"), default_handler("STRING")),
]

NEW_LINE_PATTERN = TokenPattern(r"\n")
WHITESPACE_PATTERN = TokenPattern(r"\s")


def tokenize_stream(raw_content, token_patterns):
    """
    :param raw_content: String which represents the content to tokenize.
    :param token_patterns: List of pairs (tuples): (TokenPatterns, handler function).

    :return: List of Tokens.
    """
    tokens = []
    current_index = 0
    current_column = 1
    line_number = 1

    while current_index < len(raw_content):
        current_string = raw_content[current_index:]

        # First, lets check if there are any possible matches.
        possible_matches = _get_all_possible_matches(current_string, token_patterns)
        if possible_matches:

            # 'max()' function fits our purposes.. It will choose the longest match and if there are multiple matches
            # with the same length the function will pick the first match.
            handler, lexeme = max(possible_matches, key=lambda m: len(m[1]))
            tokens.append(handler(lexeme, line_number, current_column))
            current_index += len(lexeme)
            current_column += len(lexeme)

        elif NEW_LINE_PATTERN.match(current_string):
            # If new line, increase the lines counter, set the column position to 1 and continue.
            line_number += 1
            current_index += 1
            current_column = 1

        elif WHITESPACE_PATTERN.match(current_string):
            # If whitespace then continue.
            current_index += 1
            current_column += 1

        else:
            # No match and not a whitespace. Create a special token which indicates on error in `raw_content`.
            # Then the function continues parsing the input as expected.
            tokens.append(
                Token.create_invalid_token(
                    lexeme=current_string[:1],
                    line=line_number,
                    column=current_column
                )
            )
            current_index += 1
            current_column += 1

    return tokens


def _get_all_possible_matches(string, token_patterns):
    """
    :param string: String.
    :param token_patterns: :param token_patterns: List of pairs (tuples): (TokenPatterns, handler function).

    :return:
        Returns list of pairs (handler function, lexeme), every pair represents a match (the relevant pattern matches
        the given string).
    """
    possible_matches = []

    for token_pattern, _handler in token_patterns:
        lexeme = token_pattern.match(string)
        if lexeme:
            possible_matches.append((_handler, lexeme))

    return possible_matches


def format_tokens(tokens):
    """
    Format the tokens into a nice string:
        '''
            TOKEN       LEXEME      ATTRIBUTE

            PLAYLIST    [playlist]
            NUMBER      1           1
            ...

        '''

    :param tokens: List of `Tokens`.
    :return: String.
    """
    row_template = "{:<12}  {:<12}  {:<12}\n"
    output = row_template.format("TOKEN", "LEXEME", "ATTRIBUTE") + "\n"
    for token in tokens:
        if not token.is_invalid_token():
            output += row_template.format(token.name, token.lexeme, str(token.attribute))
        else:
            output += "Error: Invalid syntax '{lexeme}' in line {line} column {column}.\n".format(
                lexeme=token.lexeme,
                line=token.line,
                column=token.column
            )

    return output


def load_file_content(filename):
    """
    :return: The content of the given `filename`.
    """
    with open(filename) as _file:
        return _file.read()


def main():
    if len(sys.argv) != 2:
        print("usage: %s <file_name>" % __file__)
    else:
        file_content = load_file_content(sys.argv[1])
        tokens = tokenize_stream(file_content, DEFAULT_TOKEN_PATTERNS)
        print(format_tokens(tokens))


if __name__ == "__main__":
    main()
