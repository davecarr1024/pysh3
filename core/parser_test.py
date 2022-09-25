'''tests for parser'''

import collections
import string
from typing import Tuple
from . import lexer, parser, stream_processor_test


class ParserTest(
    stream_processor_test.StreamProcessorTestCase[parser.lexer.Token,
                                                  parser.lexer.Token]
):
    '''tests for parser.Parser'''

    @property
    def processor(self) -> parser.Parser:
        return parser.Parser(
            'root',
            {
                'root': parser.UntilEmpty(parser.Ref('expr')),
                'expr': parser.Or([parser.Ref('id')]),
            },
            lexer.Lexer(collections.OrderedDict({
                '_ws': lexer.Class.whitespace(),
                'id': lexer.OneOrMore(lexer.Class(string.ascii_letters)),
            }))
        )

    def _result(self, rule_name: str, *children: parser.Result) -> parser.Result:
        return parser.Result(rule_name=rule_name, children=list(children))

    def _root(self, *children: parser.Result) -> parser.Result:
        return self._result('root', *children)

    def _expr(self, child: parser.Result) -> parser.Result:
        return self._result('expr', child)

    def _token(
        self,
        rule_name: str,
        value: str,
        position: lexer.Position = lexer.Position(0, 0),
    ) -> parser.Result:
        return parser.Result(value=lexer.Token(rule_name, value, position))

    def test_apply(self):
        '''tests for parser.Parser.apply'''
        for input_str, expected_result in list[Tuple[str, parser.Result]]([
            (
                'a',
                self._root(self._expr(self._token('id', 'a')))
            ),
            (
                'a b c',
                self._root(
                    self._expr(self._token('id', 'a')),
                    self._expr(self._token(
                        'id', 'b', position=lexer.Position(0, 2))),
                    self._expr(self._token(
                        'id', 'c', position=lexer.Position(0, 4))),
                )
            ),
        ]):
            with self.subTest(input_str=input_str, expected_result=expected_result):
                actual_result = self.processor.apply(input_str)
                self.assertEqual(expected_result, actual_result,
                                 f'{expected_result} != {actual_result}')
