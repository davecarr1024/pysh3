'''syntactic text parser'''

from dataclasses import dataclass
from . import lexer, stream_processor

Error = stream_processor.Error


Result = stream_processor.Result[lexer.Token]
Ref = stream_processor.Ref[lexer.Token, lexer.Token]
And = stream_processor.And[lexer.Token, lexer.Token]
Or = stream_processor.Or[lexer.Token, lexer.Token]
ZeroOrMore = stream_processor.ZeroOrMore[lexer.Token, lexer.Token]
OneOrMore = stream_processor.OneOrMore[lexer.Token, lexer.Token]
ZeroOrOne = stream_processor.ZeroOrOne[lexer.Token, lexer.Token]
UntilEmpty = stream_processor.UntilEmpty[lexer.Token, lexer.Token]


@dataclass(frozen=True)
class Parser(stream_processor.Processor[lexer.Token, lexer.Token]):
    '''generic syntactic text parser'''

    lexer: lexer.Lexer

    def apply(self, input_str: str) -> Result:
        '''apply the grammar to the input text and return the structured result'''
        try:
            char_stream = self.lexer.apply(input_str)
        except lexer.Error as error:
            raise Error(msg='lex error', children=[error]) from error
        return self.apply_root_to_state_value(char_stream)


@dataclass(frozen=True)
class Literal(stream_processor.HeadRule[lexer.Token, lexer.Token]):
    '''rule for matching tokens by rule_name'''

    rule_name: str

    def pred(self, head: lexer.Token) -> bool:
        return head.rule_name == self.rule_name

    def result(self, head: lexer.Token) -> Result:
        return Result(value=head)
