from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Mapping, MutableSequence, Optional, Sequence, TypeVar


@dataclass(frozen=True)
class Error(Exception):
    msg: Optional[str] = field(kw_only=True, default=None)
    rule_name: Optional[str] = field(kw_only=True, default=None)
    children: Sequence['Error'] = field(
        kw_only=True, default_factory=lambda: list[Error]())

    def with_rule_name(self, rule_name: str) -> 'Error':
        return Error(msg=self.msg, rule_name=rule_name, children=self.children)


_ResultValue = TypeVar('_ResultValue')
_StateValue = TypeVar('_StateValue')


@dataclass(frozen=True)
class Result(Generic[_ResultValue, _StateValue]):
    value: Optional[_ResultValue] = field(default=None, kw_only=True)
    rule_name: Optional[str] = field(kw_only=True, default=None)
    children: Sequence['Result[_ResultValue,_StateValue]'] = field(
        kw_only=True, default_factory=lambda: list[Result[_ResultValue, _StateValue]]())

    def with_rule_name(self, rule_name: str) -> 'Result[_ResultValue,_StateValue]':
        return Result[_ResultValue, _StateValue](value=self.value, rule_name=rule_name, children=self.children)


@dataclass(frozen=True, repr=False)
class State(Generic[_ResultValue, _StateValue]):
    processor: 'Processor[_ResultValue,_StateValue]'
    value: _StateValue

    def __repr__(self) -> str:
        return f'State({self.value})'


@dataclass(frozen=True)
class ResultAndState(Generic[_ResultValue, _StateValue]):
    result: Result[_ResultValue, _StateValue]
    state: State[_ResultValue, _StateValue]

    def with_rule_name(self, rule_name: str) -> 'ResultAndState[_ResultValue,_StateValue]':
        return ResultAndState[_ResultValue, _StateValue](self.result.with_rule_name(rule_name), self.state)

    def as_child_result(self) -> 'ResultAndState[_ResultValue,_StateValue]':
        return ResultAndState[_ResultValue, _StateValue](Result[_ResultValue, _StateValue](children=[self.result]), self.state)


class Rule(Generic[_ResultValue, _StateValue], ABC):
    @abstractmethod
    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]: pass


@dataclass(frozen=True)
class Processor(Generic[_ResultValue, _StateValue]):
    root_rule_name: str
    rules: Mapping[str, Rule[_ResultValue, _StateValue]]

    def apply_rule_name(self, rule_name: str, state: State[_ResultValue, _StateValue]) -> ResultAndState[_ResultValue, _StateValue]:
        if rule_name not in self.rules:
            raise Error(msg=f'unknown rule {rule_name}')
        try:
            return self.rules[rule_name].apply(state).with_rule_name(rule_name)
        except Error as error:
            raise Error(rule_name=rule_name, children=[error])

    def apply_root(self, state: State[_ResultValue, _StateValue]) -> ResultAndState[_ResultValue, _StateValue]:
        return self.apply_rule_name(self.root_rule_name, state)

    def apply(self, state_value: _StateValue) -> _ResultValue:
        result_value = self.apply_root(
            State[_ResultValue, _StateValue](self, state_value)).result.value
        if not result_value:
            raise Error(msg=f'null result')
        return result_value


@dataclass(frozen=True)
class Ref(Rule[_ResultValue, _StateValue]):
    value: str

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        return state.processor.apply_rule_name(self.value, state).as_child_result()


@dataclass(frozen=True)
class And(Rule[_ResultValue, _StateValue]):
    children: Sequence[Rule[_ResultValue, _StateValue]]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        child_results: MutableSequence[Result[_ResultValue, _StateValue]] = []
        child_state: State[_ResultValue, _StateValue] = state
        for child in self.children:
            try:
                child_result_and_state = child.apply(child_state)
                child_results.append(child_result_and_state.result)
                child_state = child_result_and_state.state
            except Error as error:
                raise Error(children=[error])
        return ResultAndState[_ResultValue, _StateValue](Result[_ResultValue, _StateValue](children=child_results), child_state)


@dataclass(frozen=True)
class Or(Rule[_ResultValue, _StateValue]):
    children: Sequence[Rule[_ResultValue, _StateValue]]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        child_errors: MutableSequence[Error] = []
        for child in self.children:
            try:
                return child.apply(state).as_child_result()
            except Error as error:
                child_errors.append(error)
        raise Error(children=child_errors)
