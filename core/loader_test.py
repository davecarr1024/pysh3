'''tests for loader'''

from collections import OrderedDict
from typing import Tuple
import unittest
from . import lexer, parser, loader

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
            ('a*', lexer.ZeroOrMore(lexer.Literal('a'))),
            ('a+', lexer.OneOrMore(lexer.Literal('a'))),
            ('a?', lexer.ZeroOrOne(lexer.Literal('a'))),
            ('a!', lexer.UntilEmpty(lexer.Literal('a'))),
            ('^a', lexer.Not(lexer.Literal('a'))),
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


class LoadParserTest(unittest.TestCase):
    '''tests for loader.load_parser'''

    def test_load(self):
        '''tests for loader.load_parser'''

        for grammar, expected_parser in list[Tuple[str, parser.Parser]]([
            (
                r'''
                a => b;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.Ref('b'),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                l = "r";
                a => b;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.Ref('b'),
                    },
                    lexer.Lexer(OrderedDict({
                        'l': lexer.Literal('r'),
                    }))
                )
            ),
            (
                r'''
                a => b c;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.And([parser.Ref('b'), parser.Ref('c')]),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                a => b | c;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.Or([parser.Ref('b'), parser.Ref('c')]),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                a => (b | c) d;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.And([
                            parser.Or([
                                parser.Ref('b'),
                                parser.Ref('c'),
                            ]),
                            parser.Ref('d'),
                        ]),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                a => b*;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.ZeroOrMore(parser.Ref('b')),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                a => (b c)*;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.ZeroOrMore(parser.And([parser.Ref('b'), parser.Ref('c')])),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                a => b* c;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.And([parser.ZeroOrMore(parser.Ref('b')), parser.Ref('c')]),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                a => b+;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.OneOrMore(parser.Ref('b')),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                a => b?;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.ZeroOrOne(parser.Ref('b')),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
            (
                r'''
                a => b!;
                ''',
                parser.Parser(
                    'a',
                    {
                        'a': parser.UntilEmpty(parser.Ref('b')),
                    },
                    lexer.Lexer(OrderedDict({}))
                )
            ),
        ]):
            with self.subTest(grammar=grammar, expected_parser=expected_parser):
                actual_parser = loader.load_parser(grammar)
                self.assertEqual(expected_parser, actual_parser,
                                 f'expected {expected_parser} != actual {actual_parser}')
