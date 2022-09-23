from dataclasses import dataclass
from typing import FrozenSet, Mapping, MutableSequence, Type
from . import stream_processor


Error = stream_processor.Error


@dataclass(frozen=True)
class Position:
    line: int
    column: int

    def __add__(self, s: str) -> 'Position':
        line = self.line
        column = self.column
        for c in s:
            if c == '\n':
                line += 1
                column = 0
            else:
                column += 1
        return Position(line, column)


@dataclass(frozen=True)
class Char:
    value: str
    position: Position

    def __post_init__(self):
        if len(self.value) != 1:
            raise Error(msg=f'invalid ResultValue value {self.value}')


CharStream = stream_processor.Stream[Char]


@dataclass(frozen=True)
class Token:
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


@dataclass(frozen=True)
class Lexer(stream_processor.Processor[Char, Char]):
    _rule_names: FrozenSet[str]

    @staticmethod
    def error_type() -> Type[Error]:
        return Error

    @staticmethod
    def build(rules: Mapping[str, Rule]) -> 'Lexer':
        return Lexer(
            '_root',
            {
                _ROOT_RULE_NAME: UntilEmpty(Ref(_TOKEN_RULE_NAME)),
                _TOKEN_RULE_NAME: Or([Ref(rule_name) for rule_name in rules.keys()]),
                **{rule_name: rule for rule_name, rule in rules.items()}
            },
            frozenset(rules.keys()),
        )

    @staticmethod
    def convert_input(input: str) -> CharStream:
        chars: MutableSequence[Char] = []
        position = Position(0, 0)
        for c in input:
            chars.append(Char(c, position))
            position += c
        return CharStream(chars)

    def convert_result(self, result: Result) -> TokenStream:
        tokens: MutableSequence[Token] = []
        for token_result in result[_TOKEN_RULE_NAME]:
            rule_result = token_result.where_one(
                Result.rule_name_in(self._rule_names))
            rule_name = rule_result.rule_name
            assert rule_name, rule_result
            chars = [char.value for char in rule_result.where(
                Result.has_value) if char.value]
            value = ''.join(char.value for char in chars)
            assert value
            tokens.append(Token(rule_name, value, chars[0].position))
        return TokenStream(tokens)

    def apply(self, input: str) -> TokenStream:
        try:
            return self.convert_result(self.apply_root_to_state_value(self.convert_input(input)))
        except stream_processor.Error as error:
            raise Error(msg=f'failed to apply regex {self} to input {repr(input)}',
                        children=[error])


@dataclass(frozen=True)
class Literal(stream_processor.HeadRule[Char, Char]):
    value: str

    def __post_init__(self):
        if len(self.value) != 1:
            raise Error(msg=f'invalid literal value {self.value}')

    def pred(self, head: Char) -> bool:
        return head.value == self.value

    def result(self, head: Char) -> Result:
        return Result(value=head)
