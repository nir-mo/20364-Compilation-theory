# File: songs_test.py
# Date: 23 - October - 2018
#
# Unittests for the implementation of a basic lexical analyzer.
#
# Author: Nir Moshe.

__author__ = "Nir Moshe"

import unittest

from songs import tokenize_stream, DEFAULT_TOKEN_PATTERNS, Token, format_tokens


INVALID_SONGS_PLAYLIST = """
    Hel$o 1:9
        "  new line \n inside string "
        
    [playlist
"""

VALID_SONGS_PLAYLIST = """
    [playlist]
      
1 [song] "Hello baby" [artist] nirmo & friends [length] 1:11
2 [song] "Ma [song] #7" [artist] 1st dude! [length]     77:17

"""


class TokenizeStreamTest(unittest.TestCase):
    def test_invalid(self):
        self.assertEqual(
            [
                Token('STRING', 'Hel', '', 2, 5),
                Token('UNKNOWN', '$', '', 2, 8),
                Token('STRING', 'o', '', 2, 9),
                Token('NUMBER', '1', 1, 2, 11),
                Token('UNKNOWN', ':', '', 2, 12),
                Token('NUMBER', '9', 9, 2, 13),
                Token('UNKNOWN', '"', '', 3, 9),
                Token('STRING', 'new', '', 3, 12),
                Token('STRING', 'line', '', 3, 16),
                Token('STRING', 'inside', '', 4, 2),
                Token('STRING', 'string', '', 4, 9),
                Token('UNKNOWN', '"', '', 4, 16),
                Token('UNKNOWN', '[', '', 6, 5),
                Token('STRING', 'playlist', '', 6, 6)
            ],
            tokenize_stream(INVALID_SONGS_PLAYLIST, DEFAULT_TOKEN_PATTERNS)
        )

    def test_keywords(self):
        self.assertEqual(
            [
                Token('PLAYLIST', '[playlist]', '', 2, 5),
                Token('NUMBER', '1', 1, 4, 1),
                Token('SONG', '[song]', '', 4, 3),
                Token('QUOTED_STRING', '"Hello baby"', 'Hello baby', 4, 10),
                Token('ARTIST', '[artist]', '', 4, 23),
                Token('STRING', 'nirmo', '', 4, 32),
                Token('STRING', '&', '', 4, 38),
                Token('STRING', 'friends', '', 4, 40),
                Token('LENGTH', '[length]', '', 4, 48),
                Token('DURATION', '1:11', '', 4, 57),
                Token('NUMBER', '2', 2, 5, 1),
                Token('SONG', '[song]', '', 5, 3),
                Token('QUOTED_STRING', '"Ma [song] #7"', 'Ma [song] #7', 5, 10),
                Token('ARTIST', '[artist]', '', 5, 25),
                Token('STRING', '1st', '', 5, 34),
                Token('STRING', 'dude!', '', 5, 38),
                Token('LENGTH', '[length]', '', 5, 44),
                Token('DURATION', '77:17', '', 5, 57)
            ],
            tokenize_stream(VALID_SONGS_PLAYLIST, DEFAULT_TOKEN_PATTERNS)
        )


class FormatTokensTest(unittest.TestCase):
    def test_invalid(self):
        self.assertEqual(
            "TOKEN         LEXEME        ATTRIBUTE   \n\nError: Invalid syntax ';' in line 1 column 1.\n",
            format_tokens([Token.create_invalid_token(";", 1, 1)])
        )

    def test_valid_string(self):
        self.assertEqual(
            'TOKEN         LEXEME        ATTRIBUTE   \n\nSONG          [song]                    \n',
            format_tokens([Token("SONG", "[song]", "", 1, 1)])
        )


if __name__ == "__main__":
    unittest.main()
