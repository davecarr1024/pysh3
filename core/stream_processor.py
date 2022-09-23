from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar
from . import processor


class Error(processor.Error):
    pass


_ResultValue = TypeVar('_ResultValue')
_Item = TypeVar('_Item')


@dataclass(frozen=True)
class Stream(Generic[_Item]):
    _items: Sequence[_Item]

    def empty(self) -> bool:
        return not self._items

    def head(self) -> _Item:
        if self.empty():
            raise Error(msg=f'getting head from empty state {self}')
        return self._items[0]

    def tail(self) -> 'Stream[_Item]':
        if self.empty():
            raise Error(msg=f'getting tail from empty state {self}')
        return Stream[_Item](self._items[1:])


Result = processor.Result[_ResultValue]
State = processor.State[_ResultValue, Stream[_Item]]
ResultAndState = processor.ResultAndState[_ResultValue, Stream[_Item]]
Rule = processor.Rule[_ResultValue, Stream[_Item]]
Processor = processor.Processor[_ResultValue, Stream[_Item]]
Ref = processor.Ref[_ResultValue, Stream[_Item]]
And = processor.And[_ResultValue, Stream[_Item]]
Or = processor.Or[_ResultValue, Stream[_Item]]
ZeroOrMore = processor.ZeroOrMore[_ResultValue, Stream[_Item]]
OneOrMore = processor.OneOrMore[_ResultValue, Stream[_Item]]
ZeroOrOne = processor.ZeroOrOne[_ResultValue, Stream[_Item]]


class UntilEmpty(processor.While[_ResultValue, Stream[_Item]]):
    def cond(self, state_value: Stream[_Item]) -> bool:
        return not state_value.empty()


class HeadRule(Rule[_ResultValue, _Item], ABC):
    @abstractmethod
    def pred(self, head: _Item) -> bool: ...

    @abstractmethod
    def result(self, head: _Item) -> Result[_ResultValue]: ...

    def apply(self, state: State[_ResultValue, _Item]) -> ResultAndState[_ResultValue, _Item]:
        if state.value.empty():
            raise Error(
                msg=f'unable to apply head rule {self} to empty state {state}')
        head: _Item = state.value.head()
        if not self.pred(head):
            raise Error(
                msg=f'failed pred for head rule {self} with head {head}')
        return ResultAndState[_ResultValue, _Item](self.result(head), state.with_value(state.value.tail()))


@dataclass(frozen=True)
class Literal(HeadRule[_ResultValue, _Item]):
    value: _Item

    def pred(self, head: _Item) -> bool:
        return head == self.value
