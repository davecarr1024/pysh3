'''generic rule-based processor'''

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Container,
    Generic,
    Iterator,
    Mapping,
    MutableSequence,
    Optional,
    Sequence,
    TypeVar,
    final,
)


def _repr(class_name: str, **fields: Any) -> str:
    fields_str = ','.join(
        [f'{name}={repr(val)}' for name, val in fields.items() if val is not None])
    return f'{class_name}({fields_str})'


@dataclass(frozen=True, repr=False)
class Error(Exception):
    '''processor error'''

    msg: Optional[str] = field(kw_only=True, default=None)
    rule_name: Optional[str] = field(kw_only=True, default=None)
    children: Sequence['Error'] = field(
        kw_only=True, default_factory=list)

    def __repr__(self) -> str:
        return _repr(
            self.__class__.__name__,
            msg=self.msg,
            rule_name=self.rule_name,
            children=self.children or None,
        )

    def __str__(self) -> str:
        return repr(self)

    def with_rule_name(self, rule_name: str) -> 'Error':
        '''annotate this error with a rule_name'''
        return self.__class__(msg=self.msg, rule_name=rule_name, children=self.children)

    def as_child_error(self) -> 'Error':
        '''returns self nested in another error, to be annotated'''
        return self.__class__(children=[self])


_ResultValue = TypeVar('_ResultValue')
_StateValue = TypeVar('_StateValue')


@final
@dataclass(frozen=True, repr=False)
class Result(Generic[_ResultValue]):
    '''a container for nested processor results'''

    value: Optional[_ResultValue] = field(default=None, kw_only=True)
    rule_name: Optional[str] = field(kw_only=True, default=None)
    children: Sequence['Result[_ResultValue]'] = field(
        kw_only=True, default_factory=lambda: list[Result[_ResultValue]]())  # pylint: disable=unnecessary-lambda

    def __repr__(self) -> str:
        return _repr(
            self.__class__.__name__,
            value=self.value,
            rule_name=self.rule_name,
            children=self.children or None,
        )

    def __str__(self) -> str:
        def _str(result: Result[_ResultValue], indent: int = 0) -> str:
            output = f'{"  "*indent}'
            if result.rule_name is not None:
                output += result.rule_name
            if result.value is not None:
                output += f'({result.value})'
            output += '\n'
            for child in result.children:
                output += _str(child, indent+1)
            return output

        return f'\n{_str(self)}'

    def with_rule_name(self, rule_name: str) -> 'Result[_ResultValue]':
        '''annotate this Result with a rule_name'''
        return Result[_ResultValue](value=self.value, rule_name=rule_name, children=self.children)

    def as_child_result(self) -> 'Result[_ResultValue]':
        '''nest this result in another result, allowing it to be annotated'''
        return Result[_ResultValue](children=[self])

    def empty(self) -> bool:
        '''is this a trivial result'''
        return (self.value is None
                and self.rule_name is None
                and all(child.empty() for child in self.children))

    def simplify(self) -> 'Result[_ResultValue]':
        '''remove trivial results from this result'''
        if self.value is None and self.rule_name is None and len(self.children) == 1:
            return self.children[0]
        return Result[_ResultValue](
            value=self.value,
            rule_name=self.rule_name,
            children=[child.simplify() for child in self.children if not child.empty()])

    @staticmethod
    def merge_children(results: Sequence['Result[_ResultValue]']) -> 'Result[_ResultValue]':
        '''merge the children of several results into one result'''
        child_results: MutableSequence[Result[_ResultValue]] = []
        for result in results:
            child_results.extend(result.children)
        return Result[_ResultValue](children=child_results)

    def where(self, cond: Callable[['Result[_ResultValue]'], bool]) -> 'Result[_ResultValue]':
        '''return the set of results in this result that match cond'''
        if cond(self):
            return self.as_child_result()
        return self.merge_children([child.where(cond) for child in self.children])

    def where_n(
        self,
        cond: Callable[['Result[_ResultValue]'], bool],
        num_results: int
    ) -> 'Result[_ResultValue]':
        '''return exactly n results in this result that match cond'''
        result = self.where(cond)
        if len(result.children) != num_results:
            raise Error(
                msg=f'expected {num_results} results got {len(result.children)}')
        return result

    def where_one(self, cond: Callable[['Result[_ResultValue]'], bool]) -> 'Result[_ResultValue]':
        '''return exactly one result in this result that matches cond (not nested)'''
        return self.where_n(cond, 1).children[0]

    @staticmethod
    def rule_name_is(rule_name: str) -> Callable[['Result[_ResultValue]'], bool]:
        '''filter for where*() that matches rule_name'''
        def closure(result: Result[_ResultValue]) -> bool:
            return result.rule_name == rule_name
        return closure

    @staticmethod
    def rule_name_in(rule_names: Container[str]) -> Callable[['Result[_ResultValue]'], bool]:
        '''filter for where*() that matches rule_name'''
        def closure(result: Result[_ResultValue]) -> bool:
            return result.rule_name in rule_names
        return closure

    @staticmethod
    def has_rule_name(result: 'Result[_ResultValue]') -> bool:
        '''filter for where*() that returns results with non-None rule_names'''
        return result.rule_name is not None

    @staticmethod
    def value_is(value: _ResultValue) -> Callable[['Result[_ResultValue]'], bool]:
        '''filter for where*() that matches value'''
        def closure(result: Result[_ResultValue]) -> bool:
            return result.value == value
        return closure

    @staticmethod
    def has_value(result: 'Result[_ResultValue]') -> bool:
        '''filter for where*() that returns results with non-None values'''
        return result.value is not None

    def all_values(self) -> Sequence[_ResultValue]:
        '''return all leaf values from this result'''
        return [
            result.value
            for result in self.where(self.has_value).children
            if result.value is not None
        ]

    def skip(self) -> 'Result[_ResultValue]':
        '''skip the current result and only consider its children'''
        return Result[_ResultValue](children=self.children)

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
    '''state container for processor

    This is distinct from _StateValue because it needs to hold a pointer back to
    the processor for rules such as Ref.
    '''

    processor: 'Processor[_ResultValue,_StateValue]'
    value: _StateValue

    def __repr__(self) -> str:
        return _repr(self.__class__.__name__, value=self.value)

    def with_value(self, value: _StateValue) -> 'State[_ResultValue,_StateValue]':
        '''returns a copy of this state with the given state

        This is useful for returning a changed state from a rule without having
        to explicitly copy the processor pointer.
        '''
        return State[_ResultValue, _StateValue](self.processor, value)


@final
@dataclass(frozen=True)
class ResultAndState(Generic[_ResultValue, _StateValue]):
    '''container for returning a result and a new state from a rule

    This is used during processing to allow both a rule's result and the state after
    processing that result to be tracked.
    '''

    result: Result[_ResultValue]
    state: State[_ResultValue, _StateValue]

    def with_rule_name(self, rule_name: str) -> 'ResultAndState[_ResultValue,_StateValue]':
        '''returns a copy of self with the result annotated with a rule_name'''
        return ResultAndState[_ResultValue, _StateValue](
            self.result.with_rule_name(rule_name),
            self.state
        )

    def as_child_result(self) -> 'ResultAndState[_ResultValue,_StateValue]':
        '''returns a copy of self with result nested'''
        return ResultAndState[_ResultValue, _StateValue](self.result.as_child_result(), self.state)

    def simplify(self) -> 'ResultAndState[_ResultValue,_StateValue]':
        '''returns a copy of self with result simplified'''
        return ResultAndState[_ResultValue, _StateValue](self.result.simplify(), self.state)


class Rule(Generic[_ResultValue, _StateValue], ABC):  # pylint: disable=too-few-public-methods
    '''interface for all processor rules'''

    @abstractmethod
    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        '''entry point for all rules

        A rule takes in the current state of the processor and returns a result
        with optional value and children and a new state.
        '''


@dataclass(frozen=True)
class Processor(Generic[_ResultValue, _StateValue]):
    '''generic processor for state that outputs result'''

    root_rule_name: str
    rules: Mapping[str, Rule[_ResultValue, _StateValue]]

    def apply_rule_name_to_state(
        self,
        rule_name: str,
        state: State[_ResultValue, _StateValue],
    ) -> ResultAndState[_ResultValue, _StateValue]:
        '''applies the rule with the given name to the given state'''
        if rule_name not in self.rules:
            raise Error(msg=f'unknown rule {rule_name}')
        try:
            return self.rules[rule_name].apply(state).with_rule_name(rule_name).simplify()
        except Error as error:
            raise error.with_rule_name(rule_name)

    def apply_root_to_state(
        self,
        state: State[_ResultValue, _StateValue],
    ) -> ResultAndState[_ResultValue, _StateValue]:
        '''applies the root rule to the given state'''
        return self.apply_rule_name_to_state(self.root_rule_name, state)

    def apply_root_to_state_value(self, state_value: _StateValue) -> Result[_ResultValue]:
        '''builds a state with the given value and applies the root rule'''
        return self.apply_root_to_state(
            State[_ResultValue, _StateValue](self, state_value)).result


@dataclass(frozen=True)
class Ref(Rule[_ResultValue, _StateValue]):
    '''a rule that defers to another rule by name

    Any results and errors are annotated with the child rule's name.
    '''

    value: str

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        '''lookup the referrant and apply it to state'''
        return state.processor.apply_rule_name_to_state(self.value, state).as_child_result()


@dataclass(frozen=True)
class And(Rule[_ResultValue, _StateValue]):
    '''applies a conjunction of rules to a state'''

    children: Sequence[Rule[_ResultValue, _StateValue]]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        '''applies all child rules in sequence and returns their results'''
        child_results: MutableSequence[Result[_ResultValue]] = []
        child_state: State[_ResultValue, _StateValue] = state
        for child in self.children:
            try:
                child_result_and_state = child.apply(child_state)
                child_results.append(child_result_and_state.result)
                child_state = child_result_and_state.state
            except Error as error:
                raise error.as_child_error() from error
        return ResultAndState[_ResultValue, _StateValue](
            Result[_ResultValue](children=child_results),
            child_state
        )


@dataclass(frozen=True)
class Or(Rule[_ResultValue, _StateValue]):
    '''applies a disjunction of rules to a state'''

    children: Sequence[Rule[_ResultValue, _StateValue]]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        '''applies child rules until one succeeds, or returns all child errors'''
        child_errors: MutableSequence[Error] = []
        for child in self.children:
            try:
                return child.apply(state).as_child_result()
            except Error as error:
                child_errors.append(error)
        raise Error(children=child_errors)


@dataclass(frozen=True)
class ZeroOrMore(Rule[_ResultValue, _StateValue]):
    '''applies a rule zero or more times'''

    child: Rule[_ResultValue, _StateValue]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        '''applies child zero or more times'''
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
    '''applies a rule one or more times'''

    child: Rule[_ResultValue, _StateValue]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        '''applies child one or more times'''
        try:
            child_result_and_state = self.child.apply(state)
            child_results: MutableSequence[Result[_ResultValue]] = [
                child_result_and_state.result]
            state = child_result_and_state.state
        except Error as error:
            raise error.as_child_error() from error
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
    '''applies a rule zero or one times'''

    child: Rule[_ResultValue, _StateValue]

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        '''applies child zero or one times'''
        try:
            return self.child.apply(state).as_child_result()
        except Error:
            return ResultAndState[_ResultValue, _StateValue](Result[_ResultValue](), state)


@dataclass(frozen=True)
class While(Rule[_ResultValue, _StateValue], ABC):
    '''applies a rule while a condition is true'''

    child: Rule[_ResultValue, _StateValue]

    @abstractmethod
    def cond(self, state_value: _StateValue) -> bool:
        '''rule eval proceeds while this returns true'''

    def apply(self, state: State[_ResultValue, _StateValue]
              ) -> ResultAndState[_ResultValue, _StateValue]:
        '''apply child as long as cond returns true'''
        child_results: MutableSequence[Result[_ResultValue]] = []
        while self.cond(state.value):
            try:
                child_result_and_state = self.child.apply(state)
            except Error as error:
                raise error.as_child_error() from error
            child_results.append(child_result_and_state.result)
            state = child_result_and_state.state
        return ResultAndState[_ResultValue, _StateValue](
            Result[_ResultValue](children=child_results), state)
