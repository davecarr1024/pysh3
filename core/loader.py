'''utils for loading lexers and parsers from text specifications'''

from collections import OrderedDict
from typing import Callable, Container, Mapping, MutableMapping, Optional, Tuple, Type, TypeVar
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
        try:
            value = result.skip().where_one(
                lambda child_result: child_result.rule_name in loaders.keys())
        except Error as error:
            raise Error(
                msg=f'failed to find operand for factory with keys {loaders.keys()} in {result}',
                children=[error]
            ) from error
        assert value.rule_name and value.rule_name in loaders, value
        return loaders[value.rule_name](value)
    return _loader


def get_token(result: parser.Result) -> lexer.Token:
    '''extract a token from a result with exactly one token in its subtree'''
    try:
        token = result.where_one(parser.Result.has_value).value
    except Error as error:
        raise Error(
            msg=f'failed to get token from result {result}', children=[error]) from error
    assert token
    return token


def get_token_value(result: parser.Result) -> str:
    '''extract a token's value from a result'''
    return get_token(result).value


def get_token_rule_name(result: parser.Result) -> str:
    '''extract a token's rule_name from a result'''
    return get_token(result).rule_name


def token_rule_name_is(rule_name: str) -> Callable[[parser.Result], bool]:
    '''predicate to be used by parser.Result.where* for filtering tokens'''
    def closure(result: parser.Result) -> bool:
        return result.value is not None and result.value.rule_name == rule_name
    return closure


def load_lex_rule(regex: str) -> lexer.Rule:
    '''load a lex rule from a regex str'''
    operators = '.\\()|[]-*+?!^'

    def load_special(result: parser.Result) -> lexer.Rule:
        value = get_token_value(result.where_one(
            parser.Result.rule_name_is('special_char')))
        special_rules = {
            'w': lexer.Class.whitespace(),
        }
        if value in special_rules:
            return special_rules[value]
        if value in operators:
            return lexer.Literal(value)
        raise Error(msg=f'invalid special char {value}')

    def load_literal(result: parser.Result) -> lexer.Rule:
        return lexer.Literal(get_token_value(result))

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
        min_result, max_result = result.where_n(token_rule_name_is('char'), 2)
        return lexer.Range(get_token_value(min_result), get_token_value(max_result))

    def load_unary_operation(rule_type: Type[lexer.UnaryRule]) -> _Loader[lexer.Token, lexer.Rule]:
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
        'zero_or_more': load_unary_operation(lexer.ZeroOrMore),
        'one_or_more': load_unary_operation(lexer.OneOrMore),
        'zero_or_one': load_unary_operation(lexer.ZeroOrOne),
        'until_empty': load_unary_operation(lexer.UntilEmpty),
        'not': load_unary_operation(lexer.Not),
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
                parser.Ref('*'),
            ]),
            'one_or_more': parser.And([
                parser.Ref('operand'),
                parser.Ref('+'),
            ]),
            'zero_or_one': parser.And([
                parser.Ref('operand'),
                parser.Ref('?'),
            ]),
            'until_empty': parser.And([
                parser.Ref('operand'),
                parser.Ref('!'),
            ]),
            'not': parser.And([
                parser.Ref('^'),
                parser.Ref('operand'),
            ]),
            'literal': parser.Ref('char'),
            'any': parser.Ref('.'),
            'special': parser.And([parser.Ref('\\'), parser.Ref('special_char')]),
            'special_char': parser.Or([
                parser.Ref('char'),
                *[parser.Ref(operator) for operator in operators]
            ]),
            'and': parser.And([
                parser.Ref('('),
                parser.OneOrMore(parser.Ref('rule')),
                parser.Ref(')'),
            ]),
            'or': parser.And([
                parser.Ref('('),
                parser.Ref('rule'),
                parser.OneOrMore(
                    parser.And([
                        parser.Ref('|'),
                        parser.Ref('rule'),
                    ])
                ),
                parser.Ref(')'),
            ]),
            'class': parser.And([
                parser.Ref('['),
                parser.OneOrMore(parser.Ref('class_part')),
                parser.Ref(']'),
            ]),
            'class_part': parser.Or([
                parser.Ref('range'),
                parser.Ref('literal'),
                parser.Ref('special'),
            ]),
            'range': parser.And([
                parser.Ref('char'),
                parser.Ref('-'),
                parser.Ref('char'),
            ]),
        },
        lexer.Lexer(OrderedDict({
            'char': lexer.Not(lexer.Class(operators)),
            **{operator: lexer.Literal(operator) for operator in operators}
        })
        )
    ).apply(regex))


def load_parser(grammar: str) -> parser.Parser:
    '''load a generic parser from a text definition'''

    operators: Container[str] = (
        '=>', '=', ';', '|', '(', ')', '*', '+', '?', '!')
    lexer_rules: OrderedDict[str, lexer.Rule] = OrderedDict[str, lexer.Rule]()

    def lexer_literal_rule(operator: str) -> lexer.Rule:
        if len(operator) == 1:
            return lexer.Literal(operator)
        return lexer.And([lexer.Literal(char) for char in operator])

    def load_lexer_rules(result: parser.Result) -> None:
        for lex_rule in result['lexer_decl']:
            name = get_token_value(
                lex_rule.where_one(token_rule_name_is('id')))
            if name in lexer_rules:
                raise Error(msg=f'duplicate lexer rule {name}')
            regex = get_token_value(lex_rule.where_one(
                token_rule_name_is('lexer_val')))[1:-1]
            lexer_rules[name] = load_lex_rule(regex)

    def load_parser_rules(result: parser.Result) -> Tuple[str, Mapping[str, parser.Rule]]:
        root_rule_name: Optional[str] = None
        rules: MutableMapping[str, parser.Rule] = {}

        def load_ref(result: parser.Result) -> parser.Rule:
            try:
                return parser.Ref(get_token_value(result))
            except Error as error:
                raise Error(
                    msg=f'failed to load ref {result}', children=[error]) from error

        def load_nary_operation(
            rule_type: Type[parser.NaryRule]
        ) -> Callable[[parser.Result], parser.Rule]:
            def closure(result: parser.Result) -> parser.Rule:
                return rule_type([load_rule(operand) for operand in result['operand']])
            return closure

        def load_unary_operation(
            rule_type: Type[parser.UnaryRule]
        ) -> Callable[[parser.Result], parser.Rule]:
            def closure(result: parser.Result) -> parser.Rule:
                return rule_type(
                    load_rule(
                        result.where_one(
                            parser.Result.rule_name_is('unary_operand'))))
            return closure

        def load_lexer_literal(result: parser.Result) -> parser.Rule:
            lexer_val = get_token_value(result)[1:-1]
            lexer_rule = lexer_literal_rule(lexer_val)
            if lexer_val in lexer_rules and lexer_rules[lexer_val] != lexer_rule:
                raise Error(
                    msg=f'mismatched lexer literal rule {lexer_val}={lexer_rule}')
            lexer_rules[lexer_val] = lexer_rule
            return parser.Ref(lexer_val)

        load_rule = factory({
            'ref': load_ref,
            'and': load_nary_operation(parser.And),
            'or': load_nary_operation(parser.Or),
            'zero_or_more': load_unary_operation(parser.ZeroOrMore),
            'one_or_more': load_unary_operation(parser.OneOrMore),
            'zero_or_one': load_unary_operation(parser.ZeroOrOne),
            'until_empty': load_unary_operation(parser.UntilEmpty),
            'lexer_literal': load_lexer_literal,
        })

        for decl in result['parser_decl']:
            try:
                name = get_token_value(decl.where_one(
                    parser.Result.rule_name_is('rule_name')))
            except Error as error:
                raise Error(
                    msg=f'failed to get rule_name in {decl}', children=[error]) from error
            if name in rules:
                raise Error(msg=f'duplicate parser rule {name}')
            if root_rule_name is None:
                root_rule_name = name
            try:
                rule_result = decl.where_one(
                    parser.Result.rule_name_is('rule'))
            except Error as error:
                raise Error(msg=f'failed to find rule in decl {decl}', children=[
                            error]) from error
            rules[name] = load_rule(rule_result)

        if root_rule_name is None:
            raise Error(msg='no root rule name found')
        return root_rule_name, rules

    result = parser.Parser(
        'root',
        {
            'root': parser.UntilEmpty(parser.Ref('line')),
            'line': parser.And([parser.Ref('decl'), parser.Ref(';')]),
            'decl': parser.Or([
                parser.Ref('lexer_decl'),
                parser.Ref('parser_decl'),
            ]),
            'lexer_decl': parser.And([
                parser.Ref('id'),
                parser.Ref('='),
                parser.Ref('lexer_val'),
            ]),
            'parser_decl': parser.And([
                parser.Ref('rule_name'),
                parser.Ref('=>'),
                parser.Ref('rule'),
            ]),
            'rule_name': parser.Ref('id'),
            'rule': parser.Or([
                parser.Ref('or'),
                parser.Ref('and'),
                parser.Ref('operand'),
            ]),
            'operand': parser.Or([
                parser.Ref('zero_or_more'),
                parser.Ref('one_or_more'),
                parser.Ref('zero_or_one'),
                parser.Ref('until_empty'),
                parser.Ref('unary_operand'),
            ]),
            'unary_operand': parser.Or([
                parser.Ref('paren_rule'),
                parser.Ref('ref'),
                parser.Ref('lexer_literal'),
            ]),
            'ref': parser.Ref('id'),
            'and': parser.And([
                parser.Ref('operand'),
                parser.OneOrMore(parser.Ref('operand')),
            ]),
            'or': parser.And([
                parser.Ref('operand'),
                parser.OneOrMore(
                    parser.And([
                        parser.Ref('|'),
                        parser.Ref('operand'),
                    ])
                )
            ]),
            'paren_rule': parser.And([
                parser.Ref('('),
                parser.Ref('rule'),
                parser.Ref(')'),
            ]),
            'zero_or_more': parser.And([
                parser.Ref('unary_operand'),
                parser.Ref('*'),
            ]),
            'one_or_more': parser.And([
                parser.Ref('unary_operand'),
                parser.Ref('+'),
            ]),
            'zero_or_one': parser.And([
                parser.Ref('unary_operand'),
                parser.Ref('?'),
            ]),
            'until_empty': parser.And([
                parser.Ref('unary_operand'),
                parser.Ref('!'),
            ]),
            'lexer_literal': parser.Ref('lexer_val'),
        },
        lexer.Lexer(OrderedDict({
            '_ws': lexer.Class.whitespace(),
            'id': load_lex_rule(r'[_a-zA-Z][_a-zA-Z0-9]*'),
            'lexer_val': load_lex_rule(r'"(^")+"'),
            **{operator: lexer_literal_rule(operator) for operator in operators}
        }))
    ).apply(grammar)

    load_lexer_rules(result)
    root_rule_name, parser_rules = load_parser_rules(result)
    return parser.Parser(root_rule_name, parser_rules, lexer.Lexer(lexer_rules))
