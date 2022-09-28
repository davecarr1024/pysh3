'''syntactic text parser'''

from dataclasses import dataclass
from typing import Type
from . import lexer, stream_processor


class Error(stream_processor.Error):
    '''parser error'''


Result = stream_processor.Result[lexer.Token]
State = stream_processor.State[lexer.Token, lexer.Token]
ResultAndState = stream_processor.ResultAndState[lexer.Token, lexer.Token]
Rule = stream_processor.Rule[lexer.Token, lexer.Token]
NaryRule = stream_processor.NaryRule[lexer.Token, lexer.Token]
UnaryRule = stream_processor.UnaryRule[lexer.Token, lexer.Token]
And = stream_processor.And[lexer.Token, lexer.Token]
Or = stream_processor.Or[lexer.Token, lexer.Token]
ZeroOrMore = stream_processor.ZeroOrMore[lexer.Token, lexer.Token]
OneOrMore = stream_processor.OneOrMore[lexer.Token, lexer.Token]
ZeroOrOne = stream_processor.ZeroOrOne[lexer.Token, lexer.Token]
UntilEmpty = stream_processor.UntilEmpty[lexer.Token, lexer.Token]
_HeadRule = stream_processor.HeadRule[lexer.Token, lexer.Token]


class StateError(Error, stream_processor.StateError[lexer.Token, lexer.Token]):  # pylint: disable=too-many-ancestors
    '''parser error with state'''

    def str_line(self, indent: int) -> str:
        output = f'\n{"  "*indent}'
        if self.rule_name:
            output += f'{self.rule_name} '
        if self.msg:
            output += f'({self.msg}) '
        if not self.state.value.empty:
            output += repr(''.join([char.value for char in self.state.value.items[:10]]))
            output += f'@{self.state.value.head.position}'
        return output


class RuleError(StateError, stream_processor.RuleError[lexer.Token, lexer.Token]):  # pylint: disable=too-many-ancestors
    '''parser error for rule'''

    def str_line(self, indent: int) -> str:
        output = f'\n{"  "*indent}'
        if self.rule_name:
            output += f'{self.rule_name} '
        output += f'for {self.rule} '
        if self.msg:
            output += f'({self.msg}) '
        if not self.state.value.empty:
            output += repr(''.join([char.value for char in self.state.value.items[:10]]))
            output += f'@{self.state.value.head.position}'
        return output


@dataclass(frozen=True)
class Parser(stream_processor.Processor[lexer.Token, lexer.Token]):
    '''generic syntactic text parser'''

    lexer: lexer.Lexer

    @staticmethod
    def error_type() -> Type[Error]:
        return Error

    def __post_init__(self):
        shared_rule_names = set(self.rules.keys()).intersection(
            self.lexer.lexer_rules().keys())
        if shared_rule_names:
            raise Error(
                msg=f'shared rule names between parser and lexer {shared_rule_names}')

    def __str__(self) -> str:
        def str_rule(name: str) -> str:
            return f'\n{name} => {self.rules[name]};'
        output = str(self.lexer)
        output += str_rule(self.root_rule_name)
        for name in self.rules.keys():
            if name != self.root_rule_name:
                output += str_rule(name)
        return output

    def apply(self, input_str: str) -> Result:
        '''apply the grammar to the input text and return the structured result'''
        return self.apply_root_to_state_value(self.lexer.apply(input_str))


@dataclass(frozen=True)
class Ref(Rule):
    '''rule for matching parser or lexer rules by name'''

    rule_name: str

    def __str__(self) -> str:
        return self.rule_name

    def apply(self, state: State) -> ResultAndState:
        assert isinstance(state.processor, Parser)
        lexer_rules = state.processor.lexer.lexer_rules()
        if self.rule_name in lexer_rules:
            if state.value.empty:
                raise RuleError(
                    rule=self,
                    state=state,
                    msg=f'failed to match parser literal {self}: empty stream',
                )
            if state.value.head.rule_name != self.rule_name:
                raise RuleError(
                    rule=self,
                    state=state,
                    msg=f'failed to match parser literal {self}',
                )
            return ResultAndState(
                Result(value=state.value.head),
                state.with_value(state.value.tail))
        return state.processor.apply_rule_name_to_state(self.rule_name, state).as_child_result()


@dataclass(frozen=True)
class Any(_HeadRule):
    '''rule for matching any token'''

    def __str__(self) -> str:
        return '.'

    def pred(self, head: lexer.Token) -> bool:
        return True

    def result(self, head: lexer.Token) -> Result:
        return Result(value=head)
