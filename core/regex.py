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
    @staticmethod
    def flatten_values(result: Result) -> str:
        s = ''
        if result.value:
            s += result.value.value
        return s + ''.join([Regex.flatten_values(child) for child in result.children])

    def apply(self, input: str) -> str:
        try:
            return self.flatten_values(self.apply_root_to_state_value(load_char_stream(input)))
        except stream_processor.Error as error:
            raise Error(msg=f'failed to apply regex {self} to input {repr(input)}',
                        children=[error])


class Literal(stream_processor.Literal[Char, Char]):
    def result(self, head: Char) -> Result:
        return Result(value=head)
