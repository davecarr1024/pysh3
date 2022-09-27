'''lexer splits an input stream in a stream of tokens'''

from dataclasses import dataclass
import string
from typing import Container, Mapping, MutableSequence, OrderedDict, Type
from . import stream_processor


class Error(stream_processor.Error):
    '''lexer error'''


@dataclass(frozen=True)
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


class StateError(stream_processor.StateError[Char]):
    '''lexer error with state'''


CharStream = stream_processor.Stream[Char]


@dataclass(frozen=True)
class Token:
    '''one item in an input document'''

    rule_name: str
    value: str
    position: Position

    def __repr__(self) -> str:
        return repr(self.value)


TokenStream = stream_processor.Stream[Token]


State = stream_processor.State[Char, Char]
Result = stream_processor.Result[Char]
ResultAndState = stream_processor.ResultAndState[Char, Char]
Rule = stream_processor.Rule[Char, Char]
Ref = stream_processor.Ref[Char, Char]
And = stream_processor.And[Char, Char]
Or = stream_processor.Or[Char, Char]
ZeroOrMore = stream_processor.ZeroOrMore[Char, Char]
OneOrMore = stream_processor.OneOrMore[Char, Char]
ZeroOrOne = stream_processor.ZeroOrOne[Char, Char]
UntilEmpty = stream_processor.UntilEmpty[Char, Char]
NaryRule = stream_processor.NaryRule[Char, Char]
UnaryRule = stream_processor.UnaryRule[Char, Char]

_INTERNAL_PREFIX = '_lexer_'
_ROOT_RULE_NAME = f'{_INTERNAL_PREFIX}root'
_TOKEN_RULE_NAME = f'{_INTERNAL_PREFIX}token'
EXCLUDE_NAME_PREFIX = '_'


@dataclass(frozen=True, init=False)
class Lexer(stream_processor.Processor[Char, Char]):
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


class _HeadRule(stream_processor.HeadRule[Char, Char]):
    def result(self, head: Char) -> Result:
        return Result(value=head)


@dataclass(frozen=True)
class Class(_HeadRule):
    '''lex rule matching range of chars'''

    values: Container[str]

    def pred(self, head: Char) -> bool:
        return head.value in self.values

    @staticmethod
    def whitespace() -> 'Class':
        '''a class for matching whitespace chars'''
        return Class(string.whitespace)


@dataclass(frozen=True)
class Literal(_HeadRule):
    '''lex rule matching a given char'''

    value: str

    def __post_init__(self):
        if len(self.value) != 1:
            raise Error(msg=f'invalid literal value {self.value}')

    def __str__(self) -> str:
        return self.value

    def pred(self, head: Char) -> bool:
        return head.value == self.value


@dataclass(frozen=True)
class Not(UnaryRule):
    '''negation of a given lex'''

    def __str__(self) -> str:
        return f'^{self.child}'

    def apply(self, state: State) -> ResultAndState:
        try:
            self.child.apply(state)
        except Error:
            return ResultAndState(
                Result(value=state.value.head),
                state.with_value(state.value.tail)
            )
        else:
            raise StateError(
                state_value=state.value,
                msg=f'Not {self} successfully applied child {self.child}',
            )


@dataclass(frozen=True)
class Any(_HeadRule):
    '''lex rule matching anything'''

    def __str__(self) -> str:
        return '.'

    def pred(self, head: Char) -> bool:
        return True


@dataclass(frozen=True)
class Range(_HeadRule):
    '''lex rule mathcing a range of chars'''

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

    def pred(self, head: Char) -> bool:
        return self.min <= head.value <= self.max
