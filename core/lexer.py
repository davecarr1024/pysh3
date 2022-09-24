'''lexer splits an input stream in a stream of tokens'''

from dataclasses import dataclass
import string
from typing import Container, MutableSequence, OrderedDict
from . import stream_processor


Error = stream_processor.Error


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


CharStream = stream_processor.Stream[Char]


@dataclass(frozen=True)
class Token:
    '''one item in an input document'''

    rule_name: str
    value: str
    position: Position


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

_ROOT_RULE_NAME = '_root'
_TOKEN_RULE_NAME = '_token'
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
        try:
            return self._convert_result(
                self.apply_root_to_state_value(
                    self._convert_input(input_str)))
        except stream_processor.Error as error:
            raise Error(
                msg=f'failed to apply regex {self} to input {repr(input_str)}',
                children=[error]) from error


@dataclass(frozen=True)
class Class(stream_processor.HeadRule[Char, Char]):
    '''lex rule matching range of chars'''

    values: Container[str]

    def pred(self, head: Char) -> bool:
        return head.value in self.values

    def result(self, head: Char) -> Result:
        return Result(value=head)

    @staticmethod
    def whitespace() -> 'Class':
        '''a class for matching whitespace chars'''
        return Class(string.whitespace)


@dataclass(frozen=True)
class Literal(stream_processor.HeadRule[Char, Char]):
    '''lex rule matching a given char'''

    value: str

    def __post_init__(self):
        if len(self.value) != 1:
            raise Error(msg=f'invalid literal value {self.value}')

    def pred(self, head: Char) -> bool:
        return head.value == self.value

    def result(self, head: Char) -> Result:
        return Result(value=head)
