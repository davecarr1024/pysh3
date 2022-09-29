'''lexer splits an input stream in a stream of tokens'''

from dataclasses import dataclass
import string
from typing import Mapping, MutableSequence, OrderedDict, Sequence, Type
from . import stream, processor


class Error(processor.Error):
    '''lexer error'''


@dataclass(frozen=True, order=True)
class Position:
    '''the position of a token in a input document'''

    line: int
    column: int

    def __add__(self, input_str: str) -> 'Position':
        line = self.line
        column = self.column
        for char in input_str:
            if char == '\n':
                line += 1
                column = 0
            else:
                column += 1
        return Position(line, column)


@dataclass(frozen=True)
class Char:
    '''one char in an incoming doc'''

    value: str
    position: Position

    def __post_init__(self):
        if len(self.value) != 1:
            raise Error(msg=f'invalid ResultValue value {self.value}')


class CharStream(stream.Stream[Char]):
    '''char stream'''

    def __str__(self) -> str:
        if self.empty:
            return 'CharStream()'
        tail_str = ''.join([char.value for char in self.items[:10]])
        return f'CharStream({repr(tail_str)}@{self.head.position})'

    @property
    def tail(self) -> 'CharStream':
        if self.empty:
            raise Error(msg='taking tail of empty stream')
        return CharStream(self._items[1:])


class StateError(Error, processor.StateError[Char, CharStream]):  # pylint: disable=too-many-ancestors
    '''lexer error with state'''


class RuleError(StateError, processor.RuleError[Char, CharStream]):  # pylint: disable=too-many-ancestors
    '''lexer error for rule'''


@dataclass(frozen=True)
class Token:
    '''one item in an input document'''

    rule_name: str
    value: str
    position: Position

    def __repr__(self) -> str:
        return repr(self.value)


class TokenStream(stream.Stream[Token]):
    '''token stream'''

    def __str__(self) -> str:
        if self.empty:
            return 'TokenStream()'
        tail_str = ' '.join([token.value for token in self.items[:10]])
        return f'TokenStream({repr(tail_str)}@{self.head.position})'

    @property
    def tail(self) -> 'TokenStream':
        if self.empty:
            raise Error(msg='taking tail of empty stream')
        return TokenStream(self._items[1:])


State = processor.State[Char, CharStream]
Result = processor.Result[Char]
ResultAndState = processor.ResultAndState[Char, CharStream]
Rule = processor.Rule[Char, CharStream]
Ref = processor.Ref[Char, CharStream]
And = processor.And[Char, CharStream]
Or = processor.Or[Char, CharStream]
ZeroOrMore = processor.ZeroOrMore[Char, CharStream]
OneOrMore = processor.OneOrMore[Char, CharStream]
ZeroOrOne = processor.ZeroOrOne[Char, CharStream]
NaryRule = processor.NaryRule[Char, CharStream]
UnaryRule = processor.UnaryRule[Char, CharStream]

_INTERNAL_PREFIX = '_lexer_'
_ROOT_RULE_NAME = f'{_INTERNAL_PREFIX}root'
_TOKEN_RULE_NAME = f'{_INTERNAL_PREFIX}token'
EXCLUDE_NAME_PREFIX = '_'


@dataclass(frozen=True, init=False)
class Lexer(processor.Processor[Char, CharStream]):
    '''Lexer splits an incoming string into tokens'''

    def __init__(self, rules: OrderedDict[str, Rule]):
        '''build a Lexer from a given set of rules'''
        super().__init__(
            _ROOT_RULE_NAME,
            {
                _ROOT_RULE_NAME: UntilEmpty(Ref(_TOKEN_RULE_NAME)),
                _TOKEN_RULE_NAME: Or([
                    Ref(rule_name)
                    for rule_name in rules.keys()
                ]),
                **rules
            },
        )

    def __str__(self) -> str:
        output = ''
        for name, rule in self.lexer_rules().items():
            output += f'\n{name} = "{rule}";'
        return output

    @staticmethod
    def error_type() -> Type[Error]:
        return Error

    def lexer_rules(self) -> Mapping[str, Rule]:
        '''get the set of rules this lexer was constructed with'''
        return {
            name: rule
            for name, rule in self.rules.items()
            if not name.startswith(_INTERNAL_PREFIX)
        }

    @staticmethod
    def _convert_input(input_str: str) -> CharStream:
        chars: MutableSequence[Char] = []
        position = Position(0, 0)
        for char in input_str:
            chars.append(Char(char, position))
            position += char
        return CharStream(chars)

    def _convert_result(self, result: Result) -> TokenStream:
        tokens: MutableSequence[Token] = []
        for token_result in result[_TOKEN_RULE_NAME]:
            rule_result = token_result.skip().where_one(Result.has_rule_name)
            rule_name = rule_result.rule_name
            assert rule_name, rule_result
            chars = rule_result.all_values()
            value = ''.join(char.value for char in chars)
            assert value
            if not rule_name.startswith(EXCLUDE_NAME_PREFIX):
                tokens.append(Token(rule_name, value, chars[0].position))
        return TokenStream(tokens)

    def apply(self, input_str: str) -> TokenStream:
        '''split an input str into a tokens'''
        return self._convert_result(
            self.apply_root_to_state_value(
                self._convert_input(input_str)))


@dataclass(frozen=True)
class Class(Rule):
    '''lex rule matching set of chars'''

    values: Sequence[str]

    def __post_init__(self):
        if not all(len(c) == 1 for c in self.values):
            raise Error(msg=f'invalid class values {repr(self.values)}')

    def apply(self, state: State) -> ResultAndState:
        if state.value.empty:
            raise RuleError(rule=self, state=state, msg='empty state')
        if state.value.head.value not in self.values:
            raise RuleError(rule=self, state=state, msg='class not found')
        return ResultAndState(Result(value=state.value.head), state.with_value(state.value.tail))

    @staticmethod
    def whitespace() -> 'Class':
        '''a class for matching whitespace chars'''
        return Class(string.whitespace)


UntilEmpty = stream.UntilEmpty[Char, CharStream]


@dataclass(frozen=True)
class Literal(Rule):
    '''lex rule matching a given char'''

    value: str

    def __post_init__(self):
        if len(self.value) != 1:
            raise Error(msg=f'invalid literal value {self.value}')

    def __str__(self) -> str:
        return self.value

    def apply(self, state: State) -> ResultAndState:
        if state.value.empty:
            raise RuleError(rule=self, state=state, msg='empty stream')
        if state.value.head.value != self.value:
            raise RuleError(rule=self, state=state)
        return ResultAndState(Result(value=state.value.head), state.with_value(state.value.tail))


@dataclass(frozen=True)
class Not(UnaryRule):
    '''negation of a lex rule'''

    def __str__(self) -> str:
        return f'^{self.child}'

    def apply(self, state: State) -> ResultAndState:
        try:
            self.child.apply(state)
        except processor.Error:
            return ResultAndState(
                Result(value=state.value.head),
                state.with_value(state.value.tail)
            )
        else:
            raise RuleError(
                rule=self,
                state=state,
                msg=f'Not {self} successfully applied child {self.child}',
            )


@dataclass(frozen=True)
class Any(Rule):
    '''lex rule matching anything'''

    def __str__(self) -> str:
        return '.'

    def apply(self, state: State) -> ResultAndState:
        if state.value.empty:
            raise RuleError(rule=self, state=state, msg='empty stream')
        return ResultAndState(Result(value=state.value.head), state.with_value(state.value.tail))


@dataclass(frozen=True)
class Range(Rule):
    '''lex rule matching a range of chars'''

    min: str
    max: str

    def __post_init__(self):
        if len(self.min) != 1:
            raise Error(msg=f'invalid min value {self.min}')
        if len(self.max) != 1:
            raise Error(msg=f'invalid max value {self.max}')
        if self.min >= self.max:
            raise Error(msg=f'invalid range {self}')

    def __str__(self) -> str:
        return f'[{self.min}-{self.max}]'

    def apply(self, state: State) -> ResultAndState:
        if state.value.empty:
            raise RuleError(rule=self, state=state, msg='empty stream')
        if state.value.head.value < self.min or state.value.head.value > self.max:
            raise RuleError(rule=self, state=state)
        return ResultAndState(Result(value=state.value.head), state.with_value(state.value.tail))
