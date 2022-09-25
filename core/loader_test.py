'''tests for loader'''

from typing import Tuple
import unittest
from . import loader, lexer

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    # pylint: disable=protected-access
    __import__(
        'sys').modules['unittest.util']._MAX_LENGTH = 999999999
    # pylint: enable=protected-access


class LoadLexRuleTest(unittest.TestCase):
    '''tests for loader.load_lex_rule'''

    def test_load(self):
        '''tests for loader.load_lex_rule'''
        for regex, expected_lex_rule in list[Tuple[str, lexer.Rule]]([
            ('a', lexer.Literal('a')),
            ('.', lexer.Any()),
            ('\\w', lexer.Class.whitespace()),
            ('\\.', lexer.Literal('.')),
            ('(ab)', lexer.And([lexer.Literal('a'), lexer.Literal('b')])),
            ('(a|b)', lexer.Or([lexer.Literal('a'), lexer.Literal('b')])),
            ('[ab]', lexer.Or([lexer.Literal('a'), lexer.Literal('b')])),
            ('[a-z]', lexer.Range('a', 'z')),
            ('[a-zA-Z]', lexer.Or([lexer.Range('a', 'z'), lexer.Range('A', 'Z')])),
        ]):
            with self.subTest(regex=regex, expected_lex_rule=expected_lex_rule):
                actual_lex_rule = loader.load_lex_rule(regex)
                self.assertEqual(expected_lex_rule, actual_lex_rule,
                                 f'expected {expected_lex_rule} != actual {actual_lex_rule}')

    def test_load_fail(self):
        '''tests for loader.load_lex_rule failures'''
        for regex in list[str]([
            '\\a',
        ]):
            with self.subTest(regex=regex):
                with self.assertRaises(loader.Error):
                    loader.load_lex_rule(regex)
