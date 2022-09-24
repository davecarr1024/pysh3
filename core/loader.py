'''utils for loading lexers and parsers from text specifications'''

from collections import OrderedDict
from typing import Callable, Mapping, TypeVar
from . import lexer, parser, processor

_ResultValue = TypeVar('_ResultValue')
_Result = processor.Result[_ResultValue]
_FactoryItem = TypeVar('_FactoryItem')
_Loader = Callable[[_Result[_ResultValue]], _FactoryItem]


def factory(
    loaders: Mapping[str, _Loader[_ResultValue, _FactoryItem]],
) -> _Loader[_ResultValue, _FactoryItem]:
    '''generic result factory triggered by result rule_name'''
    def _loader(result: _Result[_ResultValue]) -> _FactoryItem:
        value = result.skip().where_one(
            lambda child_result: child_result.rule_name in loaders.keys())
        assert value.rule_name and value.rule_name in loaders, value
        return loaders[value.rule_name](value)
    return _loader


def load_lex_rule(regex: str) -> lexer.Rule:
    '''load a lex rule from a regex str'''
    operators = '()[-]*+?!^.'
    result = parser.Parser(
        'root',
        {
            'root': parser.UntilEmpty(parser.Ref('rule')),
            'rule': parser.Or([parser.Ref('operand')]),
            'operand': parser.Or([
                parser.Ref('literal'),
                parser.Ref('any'),
            ]),
            'literal': parser.Literal('char'),
            'any': parser.Literal('.'),
        },
        lexer.Lexer(OrderedDict({
            'char': lexer.Not(lexer.Class(operators)),
            **{operator: lexer.Literal(operator) for operator in operators}
        })
        )
    ).apply(regex)

    def load_literal(result: parser.Result) -> lexer.Rule:
        assert result.value, result
        return lexer.Literal(result.value.value)

    def load_rule(result: parser.Result) -> lexer.Rule:
        return factory({
            'literal': load_literal,
            'any': lambda _: lexer.Any(),
        })(result)

    def load_and(result: parser.Result) -> lexer.And:
        return lexer.And([load_rule(rule) for rule in result['rule']])

    lex_rule = load_and(result)
    if len(lex_rule.children) == 1:
        return lex_rule.children[0]
    return lex_rule
