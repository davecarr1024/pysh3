'''syntactic text parser'''

from dataclasses import dataclass
from typing import Type
from . import processor, lexer, stream


class Error(processor.Error):
    '''parser error'''


Result = processor.Result[lexer.Token]
State = processor.State[lexer.Token, lexer.TokenStream]
ResultAndState = processor.ResultAndState[lexer.Token, lexer.TokenStream]
Rule = processor.Rule[lexer.Token, lexer.TokenStream]
NaryRule = processor.NaryRule[lexer.Token, lexer.TokenStream]
UnaryRule = processor.UnaryRule[lexer.Token, lexer.TokenStream]
And = processor.And[lexer.Token, lexer.TokenStream]
Or = processor.Or[lexer.Token, lexer.TokenStream]
ZeroOrMore = processor.ZeroOrMore[lexer.Token, lexer.TokenStream]
OneOrMore = processor.OneOrMore[lexer.Token, lexer.TokenStream]
ZeroOrOne = processor.ZeroOrOne[lexer.Token, lexer.TokenStream]


class StateError(Error, processor.StateError[lexer.Token, lexer.TokenStream]):  # pylint: disable=too-many-ancestors
    '''parser error with state'''


class RuleError(StateError, processor.RuleError[lexer.Token, lexer.TokenStream]):  # pylint: disable=too-many-ancestors
    '''parser error for rule'''


@dataclass(frozen=True)
class Parser(processor.Processor[lexer.Token, lexer.TokenStream]):
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


UntilEmpty = stream.UntilEmpty[lexer.Token, lexer.TokenStream]
Any = stream.Any[lexer.Token]
