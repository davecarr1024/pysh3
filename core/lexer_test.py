'''tests for lexer module'''

from typing import Tuple
import unittest

from . import lexer, stream_processor_test


class CharTest(unittest.TestCase):
    '''tests for lexer.Char'''

    def test_ctor(self):
        '''test that lexer.Char ctor accepts one char'''
        lexer.Char('a', lexer.Position(0, 0))

    def test_ctor_fail(self):
        '''test that lexer.Char fails with invalid values'''
        with self.assertRaises(lexer.Error):
            lexer.Char('', lexer.Position(0, 0))
        with self.assertRaises(lexer.Error):
            lexer.Char('aa', lexer.Position(0, 0))


_StreamProcessorTestCase = stream_processor_test.StreamProcessorTestCase[
    lexer.Char, lexer.Char]


class LexerTest(_StreamProcessorTestCase):
    '''tests for lexer.Lexer'''

    @property
    def processor(self) -> lexer.Lexer:
        return lexer.Lexer.build({
            'a': lexer.Literal('a'),
            'b': lexer.And([lexer.Literal('b'), lexer.Literal('b')]),
            'c': lexer.Or([lexer.Literal('c'), lexer.Literal('C')]),
            'd': lexer.And([
                lexer.Literal('d'),
                lexer.ZeroOrMore(lexer.Literal('D')),
            ]),
            'e': lexer.And([
                lexer.Literal('e'),
                lexer.ZeroOrOne(lexer.Literal('E')),
            ]),
            'f': lexer.OneOrMore(lexer.Literal('f')),
            '_g': lexer.Literal('g'),
        })

    def test_apply(self):
        '''test successful apply cases'''
        for input_str, expected in list[Tuple[str, lexer.TokenStream]]([
            (
                'a',
                lexer.TokenStream([
                    lexer.Token(rule_name='a', value='a',
                                position=lexer.Position(0, 0)),
                ])
            ),
            (
                'bb',
                lexer.TokenStream([
                    lexer.Token(rule_name='b', value='bb',
                                position=lexer.Position(0, 0)),
                ])
            ),
            (
                'abba',
                lexer.TokenStream([
                    lexer.Token(rule_name='a', value='a',
                                position=lexer.Position(0, 0)),
                    lexer.Token(rule_name='b', value='bb',
                                position=lexer.Position(0, 1)),
                    lexer.Token(rule_name='a', value='a',
                                position=lexer.Position(0, 3)),
                ])
            ),
            (
                'cC',
                lexer.TokenStream([
                    lexer.Token(rule_name='c', value='c',
                                position=lexer.Position(0, 0)),
                    lexer.Token(rule_name='c', value='C',
                                position=lexer.Position(0, 1)),
                ])
            ),
            (
                'd',
                lexer.TokenStream([
                    lexer.Token(rule_name='d', value='d',
                                position=lexer.Position(0, 0)),
                ])
            ),
            (
                'dDDD',
                lexer.TokenStream([
                    lexer.Token(rule_name='d', value='dDDD',
                                position=lexer.Position(0, 0)),
                ])
            ),
            (
                'e',
                lexer.TokenStream([
                    lexer.Token(rule_name='e', value='e',
                                position=lexer.Position(0, 0)),
                ])
            ),
            (
                'eE',
                lexer.TokenStream([
                    lexer.Token(rule_name='e', value='eE',
                                position=lexer.Position(0, 0)),
                ])
            ),
            (
                'f',
                lexer.TokenStream([
                    lexer.Token(rule_name='f', value='f',
                                position=lexer.Position(0, 0)),
                ])
            ),
            (
                'fff',
                lexer.TokenStream([
                    lexer.Token(rule_name='f', value='fff',
                                position=lexer.Position(0, 0)),
                ])
            ),
            (
                'aga',
                lexer.TokenStream([
                    lexer.Token(rule_name='a', value='a',
                                position=lexer.Position(0, 0)),
                    lexer.Token(rule_name='a', value='a',
                                position=lexer.Position(0, 2)),
                ])
            ),
        ]):
            with self.subTest(input=input_str, expected=expected):
                actual = self.processor.apply(input_str)
                self.assertEqual(expected, actual)

    def test_apply_fail(self):
        '''test failing apply cases'''
        with self.assertRaises(lexer.Error):
            self.processor.apply('z')
