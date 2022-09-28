'''generic processor for streaming input'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence, Type, TypeVar
from . import processor


class Error(processor.Error):
    '''stream_processor error'''


_ResultValue = TypeVar('_ResultValue')
_Item = TypeVar('_Item')


@dataclass(frozen=True)
class Stream(Iterable[_Item]):
    '''generic stream of incoming input items'''

    _items: Sequence[_Item]

    def __iter__(self) -> Iterator[_Item]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __str__(self) -> str:
        return str(self.items)

    @property
    def empty(self) -> bool:
        '''is this stream empty'''
        return len(self) == 0

    @property
    def head(self) -> _Item:
        '''the first value in the stream'''
        if self.empty:
            raise Error(msg=f'getting head from empty state {self}')
        return self._items[0]

    @property
    def tail(self) -> 'Stream[_Item]':
        '''all but the first value in the stream'''
        if self.empty:
            raise Error(msg=f'getting tail from empty state {self}')
        return Stream[_Item](self._items[1:])

    @property
    def items(self) -> 'Sequence[_Item]':
        '''items'''
        return self._items

    @staticmethod
    def from_result(result: processor.Result[_Item]) -> 'Stream[_Item]':
        '''convert all results in the given result to a stream'''
        return Stream[_Item](result.all_values())


class StateError(Error, processor.StateError[_ResultValue, Stream[_Item]]):  # pylint: disable=too-many-ancestors
    '''error with state'''


class RuleError(StateError[_ResultValue, _Item], processor.RuleError[_ResultValue, Stream[_Item]]):  # pylint: disable=too-many-ancestors
    '''error for rule'''


Result = processor.Result[_ResultValue]
State = processor.State[_ResultValue, Stream[_Item]]
ResultAndState = processor.ResultAndState[_ResultValue, Stream[_Item]]
Rule = processor.Rule[_ResultValue, Stream[_Item]]
Ref = processor.Ref[_ResultValue, Stream[_Item]]
And = processor.And[_ResultValue, Stream[_Item]]
Or = processor.Or[_ResultValue, Stream[_Item]]
ZeroOrMore = processor.ZeroOrMore[_ResultValue, Stream[_Item]]
OneOrMore = processor.OneOrMore[_ResultValue, Stream[_Item]]
ZeroOrOne = processor.ZeroOrOne[_ResultValue, Stream[_Item]]
NaryRule = processor.NaryRule[_ResultValue, Stream[_Item]]
UnaryRule = processor.UnaryRule[_ResultValue, Stream[_Item]]


class Processor(processor.Processor[_ResultValue, Stream[_Item]]):
    '''generic stream processor'''

    @staticmethod
    def error_type() -> Type[Error]:
        return Error


class UntilEmpty(processor.While[_ResultValue, Stream[_Item]]):
    '''rule for processing items from the input stream until empty'''

    def cond(self, state_value: Stream[_Item]) -> bool:
        return not state_value.empty


class HeadRule(Rule[_ResultValue, _Item], ABC):
    '''generic rule for operating on the head value of a stream'''

    @abstractmethod
    def pred(self, head: _Item) -> bool:
        '''only process the head value if this is true'''

    @abstractmethod
    def result(self, head: _Item) -> Result[_ResultValue]:
        '''convert the head value to a Result'''

    def apply(self, state: State[_ResultValue, _Item]) -> ResultAndState[_ResultValue, _Item]:
        '''process the head value and return the result'''
        if state.value.empty:
            raise RuleError(
                rule=self,
                state=state,
                msg=f'failed {self}: empty stream',
            )
        head: _Item = state.value.head
        if not self.pred(head):
            raise RuleError(
                rule=self,
                state=state,
                msg=f'failed {self}',
            )
        return ResultAndState[_ResultValue, _Item](
            self.result(head),
            state.with_value(state.value.tail)
        )


@dataclass(frozen=True)
class Literal(HeadRule[_ResultValue, _Item]):
    '''generic rule for matching the head of the stream to a given value'''

    value: _Item

    def pred(self, head: _Item) -> bool:
        '''returns true if the stream head matches the given value'''
        return head == self.value
