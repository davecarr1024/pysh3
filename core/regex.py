from dataclasses import dataclass
from . import stream_processor


class Error(stream_processor.Error):
    pass


@dataclass(frozen=True)
class Char:
    value: str

    def __post_init__(self):
        if len(self.value) != 1:
            raise Error(msg=f'invalid ResultValue value {self.value}')


CharStream = stream_processor.Stream[Char]


def load_char_stream(input: str) -> CharStream:
    return CharStream([Char(c) for c in input])


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


class Regex(stream_processor.Processor[Char, Char]):
    def apply(self, input: str) -> str:
        try:
            result = self.apply_root_to_state_value(load_char_stream(input))
        except stream_processor.Error as error:
            raise Error(msg=f'failed to apply regex {self} to input {repr(input)}',
                        children=[error])
        return ''.join([value.value for value in result.all_values()])


class Literal(stream_processor.Literal[Char, Char]):
    def result(self, head: Char) -> Result:
        return Result(value=head)
