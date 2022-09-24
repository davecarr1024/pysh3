'''tests for loader'''

from typing import Tuple
import unittest
from . import loader, lexer


class LoadLexRuleTest(unittest.TestCase):
    '''tests for loader.load_lex_rule'''

    def test_load(self):
        '''tests for loader.load_lex_rule'''
        for regex, expected_lex_rule in list[Tuple[str, lexer.Rule]]([
            ('a', lexer.Literal('a')),
            ('.', lexer.Any()),
        ]):
            with self.subTest(regex=regex, expected_lex_rule=expected_lex_rule):
                actual_lex_rule = loader.load_lex_rule(regex)
                self.assertEqual(expected_lex_rule, actual_lex_rule)
