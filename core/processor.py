from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Container, Generic, Iterator, Mapping, MutableSequence, Optional, Sequence, Type, TypeVar, final


def _repr(class_name: str, **fields: Any) -> str:
    fields_str = ','.join(
        [f'{name}={repr(val)}' for name, val in fields.items() if val is not None])
    return f'{class_name}({fields_str})'


@dataclass(frozen=True, repr=False)
class Error(Exception):
    msg: Optional[str] = field(kw_only=True, default=None)
    rule_name: Optional[str] = field(kw_only=True, default=None)
    children: Sequence['Error'] = field(
        kw_only=True, default_factory=list)

    def __repr__(self) -> str:
        return _repr(self.__class__.__name__, msg=self.msg, rule_name=self.rule_name, children=self.children or None)

    def __str__(self) -> str:
        return repr(self)

    def with_rule_name(self, rule_name: str) -> 'Error':
        return self.__class__(msg=self.msg, rule_name=rule_name, children=self.children)


_ResultValue = TypeVar('_ResultValue')
_StateValue = TypeVar('_StateValue')


@final
@dataclass(frozen=True, repr=False)
class Result(Generic[_ResultValue]):
    value: Optional[_ResultValue] = field(default=None, kw_only=True)
    rule_name: Optional[str] = field(kw_only=True, default=None)
    children: Sequence['Result[_ResultValue]'] = field(
        kw_only=True, default_factory=lambda: list[Result[_ResultValue]]())  # pylint: disable=unnecessary-lambda

    def __repr__(self) -> str:
        return _repr(self.__class__.__name__, value=self.value, rule_name=self.rule_name, children=self.children or None)

    def with_rule_name(self, rule_name: str) -> 'Result[_ResultValue]':
        '''Annotate this Result with a rule_name.'''
        return Result[_ResultValue](value=self.value, rule_name=rule_name, children=self.children)

    def as_child_result(self) -> 'Result[_ResultValue]':
        '''Nest this result in another result, allowing it to be annotated.'''
        return Result[_ResultValue](children=[self])

    def empty(self) -> bool:
        '''Is this a trivial result.'''
        return (self.value is None
                and self.rule_name is None
                and all([child.empty() for child in self.children]))

    def simplify(self) -> 'Result[_ResultValue]':
        '''Remove trivial results from this result.'''
        if self.value is None and self.rule_name is None and len(self.children) == 1:
            return self.children[0]
        else:
            return Result[_ResultValue](
                value=self.value,
                rule_name=self.rule_name,
                children=[child.simplify() for child in self.children if not child.empty()])

    @staticmethod
    def merge_children(results: Sequence['Result[_ResultValue]']) -> 'Result[_ResultValue]':
        child_results: MutableSequence[Result[_ResultValue]] = []
        for result in results:
            child_results.extend(result.children)
        return Result[_ResultValue](children=child_results)

    def where(self, cond: Callable[['Result[_ResultValue]'], bool]) -> 'Result[_ResultValue]':
        if cond(self):
            return self.as_child_result()
        return self.merge_children([child.where(cond) for child in self.children])

    def where_n(self, cond: Callable[['Result[_ResultValue]'], bool], n: int) -> 'Result[_ResultValue]':
        result = self.where(cond)
        if len(result.children) != n:
            raise Error(msg=f'expected {n} results got {len(result.children)}')
        return result

    def where_one(self, cond: Callable[['Result[_ResultValue]'], bool]) -> 'Result[_ResultValue]':
        return self.where_n(cond, 1).children[0]

    @staticmethod
    def rule_name_is(rule_name: str) -> Callable[['Result[_ResultValue]'], bool]:
        def closure(result: Result[_ResultValue]) -> bool:
            return result.rule_name == rule_name
        return closure

    @staticmethod
    def rule_name_in(rule_names: Container[str]) -> Callable[['Result[_ResultValue]'], bool]:
        def closure(result: Result[_ResultValue]) -> bool:
            return result.rule_name in rule_names
        return closure

    @staticmethod
    def value_is(value: _ResultValue) -> Callable[['Result[_ResultValue]'], bool]:
        def closure(result: Result[_ResultValue]) -> bool:
            return result.value == value
        return closure

    @staticmethod
    def has_value(result: 'Result[_ResultValue]') -> bool:
        return result.value is not None

    def all_values(self) -> Sequence[_ResultValue]:
        return [result.value for result in self.where(self.has_value).children if result.value is not None]

    def __iter__(self) -> Iterator['Result[_ResultValue]']:
        return iter(self.children)

    def __getitem__(self, rule_name: str) -> 'Result[_ResultValue]':
        return self.where(self.rule_name_is(rule_name))

    def __len__(self) -> int:
        return len(self.children)

    def __contains__(self, rule_name: str) -> bool:
        return len(self[rule_name]) > 0


@final
@dataclass(frozen=True, repr=False)
class State(Generic[_ResultValue, _StateValue]):
    processor: 'Processor[_ResultValue,_StateValue]'
    value: _StateValue

    def __repr__(self) -> str:
        return _repr(self.__class__.__name__, value=self.value)

    def with_value(self, value: _StateValue) -> 'State[_ResultValue,_StateValue]':
        return State[_ResultValue, _StateValue](self.processor, value)


@final
@dataclass(frozen=True)
class ResultAndState(Generic[_ResultValue, _StateValue]):
    result: Result[_ResultValue]
    state: State[_ResultValue, _StateValue]

    def with_rule_name(self, rule_name: str) -> 'ResultAndState[_ResultValue,_StateValue]':
        return ResultAndState[_ResultValue, _StateValue](self.result.with_rule_name(rule_name), self.state)

    def as_child_result(self) -> 'ResultAndState[_ResultValue,_StateValue]':
        return ResultAndState[_ResultValue, _StateValue](self.result.as_child_result(), self.state)

    def simplify(self) -> 'ResultAndState[_ResultValue,_StateValue]':
        return ResultAndState[_ResultValue, _StateValue](self.result.simplify(), self.state)


class Rule(Generic[_ResultValue, _StateValue], ABC):
    @abstractmethod
    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]: ...


@dataclass(frozen=True)
class Processor(Generic[_ResultValue, _StateValue]):
    root_rule_name: str
    rules: Mapping[str, Rule[_ResultValue, _StateValue]]

    @staticmethod
    def error_type() -> Type[Error]:
        return Error

    def apply_rule_name_to_state(self, rule_name: str, state: State[_ResultValue, _StateValue]) -> ResultAndState[_ResultValue, _StateValue]:
        if rule_name not in self.rules:
            raise Error(msg=f'unknown rule {rule_name}')
        try:
            return self.rules[rule_name].apply(state).with_rule_name(rule_name).simplify()
        except Error as error:
            raise error.with_rule_name(rule_name)

    def apply_root_to_state(self, state: State[_ResultValue, _StateValue]) -> ResultAndState[_ResultValue, _StateValue]:
        return self.apply_rule_name_to_state(self.root_rule_name, state)

    def apply_root_to_state_value(self, state_value: _StateValue) -> Result[_ResultValue]:
        return self.apply_root_to_state(
            State[_ResultValue, _StateValue](self, state_value)).result


@dataclass(frozen=True)
class Ref(Rule[_ResultValue, _StateValue]):
    value: str

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        return state.processor.apply_rule_name_to_state(self.value, state).as_child_result()


@dataclass(frozen=True)
class And(Rule[_ResultValue, _StateValue]):
    children: Sequence[Rule[_ResultValue, _StateValue]]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        child_results: MutableSequence[Result[_ResultValue]] = []
        child_state: State[_ResultValue, _StateValue] = state
        for child in self.children:
            try:
                child_result_and_state = child.apply(child_state)
                child_results.append(child_result_and_state.result)
                child_state = child_result_and_state.state
            except Error as error:
                raise Error(children=[error]) from error
        return ResultAndState[_ResultValue, _StateValue](Result[_ResultValue](children=child_results), child_state)


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


@dataclass(frozen=True)
class ZeroOrMore(Rule[_ResultValue, _StateValue]):
    child: Rule[_ResultValue, _StateValue]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        child_results: MutableSequence[Result[_ResultValue]] = []
        while True:
            try:
                child_result_and_state = self.child.apply(state)
                child_results.append(child_result_and_state.result)
                state = child_result_and_state.state
            except Error:
                return ResultAndState[_ResultValue, _StateValue](
                    Result[_ResultValue](children=child_results), state)


@dataclass(frozen=True)
class OneOrMore(Rule[_ResultValue, _StateValue]):
    child: Rule[_ResultValue, _StateValue]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        try:
            child_result_and_state = self.child.apply(state)
            child_results: MutableSequence[Result[_ResultValue]] = [
                child_result_and_state.result]
            state = child_result_and_state.state
        except Error as error:
            raise Error(children=[error]) from error
        while True:
            try:
                child_result_and_state = self.child.apply(state)
                child_results.append(child_result_and_state.result)
                state = child_result_and_state.state
            except Error:
                break
        return ResultAndState(Result(children=child_results), state)


@dataclass(frozen=True)
class ZeroOrOne(Rule[_ResultValue, _StateValue]):
    child: Rule[_ResultValue, _StateValue]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        try:
            return self.child.apply(state).as_child_result()
        except Error:
            return ResultAndState[_ResultValue, _StateValue](Result[_ResultValue](), state)


@dataclass(frozen=True)
class While(Rule[_ResultValue, _StateValue], ABC):
    child: Rule[_ResultValue, _StateValue]

    @abstractmethod
    def cond(self, state_value: _StateValue) -> bool: ...

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        child_results: MutableSequence[Result[_ResultValue]] = []
        while self.cond(state.value):
            child_result_and_state = self.child.apply(state)
            child_results.append(child_result_and_state.result)
            state = child_result_and_state.state
        return ResultAndState[_ResultValue, _StateValue](
            Result[_ResultValue](children=child_results), state)
