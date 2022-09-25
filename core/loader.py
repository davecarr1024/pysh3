'''utils for loading lexers and parsers from text specifications'''

from collections import OrderedDict
from typing import Callable, Mapping, Type, TypeVar
from . import lexer, parser, processor

Error = processor.Error

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
    operators = '.\\()|[]-*+?!^'

    def load_special(result: parser.Result) -> lexer.Rule:
        special_char = result.where_one(
            parser.Result.rule_name_is('special_char')).where_one(parser.Result.has_value)
        assert special_char.value
        value = special_char.value.value
        special_rules = {
            'w': lexer.Class.whitespace(),
        }
        if value in special_rules:
            return special_rules[value]
        if value in operators:
            return lexer.Literal(value)
        raise Error(msg=f'invalid special char {value}')

    def load_literal(result: parser.Result) -> lexer.Rule:
        assert result.value, result
        return lexer.Literal(result.value.value)

    def load_and(result: parser.Result) -> lexer.Rule:
        rule = lexer.And([load_rule(rule) for rule in result['rule']])
        if len(rule.children) == 1:
            return rule.children[0]
        return rule

    def load_or(result: parser.Result) -> lexer.Rule:
        return lexer.Or([load_rule(rule) for rule in result['rule']])

    def load_class(result: parser.Result) -> lexer.Rule:
        rule = lexer.Or([load_class_part(rule)
                        for rule in result['class_part']])
        if len(rule.children) == 1:
            return rule.children[0]
        return rule

    def load_range(result: parser.Result) -> lexer.Rule:
        min_result, _, max_result = result.where_n(parser.Result.has_value, 3)
        assert min_result.value and max_result.value
        return lexer.Range(min_result.value.value, max_result.value.value)

    def unary_operation(rule_type: Type[lexer.UnaryRule]) -> _Loader[lexer.Token, lexer.Rule]:
        def load(result: parser.Result) -> lexer.Rule:
            return rule_type(load_rule(result.where_one(parser.Result.rule_name_is('operand'))))
        return load

    load_rule = factory({
        'literal': load_literal,
        'any': lambda _: lexer.Any(),
        'special': load_special,
        'and': load_and,
        'or': load_or,
        'class': load_class,
        'zero_or_more': unary_operation(lexer.ZeroOrMore),
        'one_or_more': unary_operation(lexer.OneOrMore),
        'zero_or_one': unary_operation(lexer.ZeroOrOne),
        'until_empty': unary_operation(lexer.UntilEmpty),
        'not': unary_operation(lexer.Not),
    })

    load_class_part = factory({
        'literal': load_literal,
        'special': load_special,
        'range': load_range,
    })

    return load_and(parser.Parser(
        'root',
        {
            'root': parser.UntilEmpty(parser.Ref('rule')),
            'rule': parser.Or([
                parser.Ref('operation'),
                parser.Ref('operand'),
            ]),
            'operand': parser.Or([
                parser.Ref('literal'),
                parser.Ref('any'),
                parser.Ref('special'),
                parser.Ref('and'),
                parser.Ref('or'),
                parser.Ref('class'),
            ]),
            'operation': parser.Or([
                parser.Ref('zero_or_more'),
                parser.Ref('one_or_more'),
                parser.Ref('zero_or_one'),
                parser.Ref('until_empty'),
                parser.Ref('not'),
            ]),
            'zero_or_more': parser.And([
                parser.Ref('operand'),
                parser.Literal('*'),
            ]),
            'one_or_more': parser.And([
                parser.Ref('operand'),
                parser.Literal('+'),
            ]),
            'zero_or_one': parser.And([
                parser.Ref('operand'),
                parser.Literal('?'),
            ]),
            'until_empty': parser.And([
                parser.Ref('operand'),
                parser.Literal('!'),
            ]),
            'not': parser.And([
                parser.Literal('^'),
                parser.Ref('operand'),
            ]),
            'literal': parser.Literal('char'),
            'any': parser.Literal('.'),
            'special': parser.And([parser.Literal('\\'), parser.Ref('special_char')]),
            'special_char': parser.Or([
                parser.Literal('char'),
                *[parser.Literal(operator) for operator in operators]
            ]),
            'and': parser.And([
                parser.Literal('('),
                parser.OneOrMore(parser.Ref('rule')),
                parser.Literal(')'),
            ]),
            'or': parser.And([
                parser.Literal('('),
                parser.Ref('rule'),
                parser.OneOrMore(
                    parser.And([
                        parser.Literal('|'),
                        parser.Ref('rule'),
                    ])
                ),
                parser.Literal(')'),
            ]),
            'class': parser.And([
                parser.Literal('['),
                parser.OneOrMore(parser.Ref('class_part')),
                parser.Literal(']'),
            ]),
            'class_part': parser.Or([
                parser.Ref('range'),
                parser.Ref('literal'),
                parser.Ref('special'),
            ]),
            'range': parser.And([
                parser.Literal('char'),
                parser.Literal('-'),
                parser.Literal('char'),
            ]),
        },
        lexer.Lexer(OrderedDict({
            'char': lexer.Not(lexer.Class(operators)),
            **{operator: lexer.Literal(operator) for operator in operators}
        })
        )
    ).apply(regex))
