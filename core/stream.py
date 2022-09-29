'''stream state value'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Iterator, MutableSequence, Sequence, TypeVar
from . import processor


class Error(processor.Error):
    '''stream error'''


_Item_co = TypeVar('_Item_co', covariant=True)


class AbstractStream(ABC):
    '''abstract stream'''

    @property
    @abstractmethod
    def empty(self) -> bool:
        '''is this stream empty'''


@dataclass(frozen=True)
class Stream(AbstractStream, Iterable[_Item_co]):
    '''generic stream of incoming input items'''

    _items: Sequence[_Item_co]

    def __iter__(self) -> Iterator[_Item_co]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __str__(self) -> str:
        return str(self.items)

    @property
    def empty(self) -> bool:
        return len(self) == 0

    @property
    def head(self) -> _Item_co:
        '''the first value in the stream'''
        if self.empty:
            raise Error(msg=f'getting head from empty state {self}')
        return self._items[0]

    @property
    def tail(self) -> 'Stream[_Item_co]':
        '''all but the first value in the stream'''
        if self.empty:
            raise Error(msg=f'getting tail from empty state {self}')
        return Stream[_Item_co](self._items[1:])

    @property
    def items(self) -> 'Sequence[_Item_co]':
        '''items'''
        return self._items

    @staticmethod
    def from_result(result: processor.Result[_Item_co]) -> 'Stream[_Item_co]':
        '''convert all results in the given result to a stream'''
        return Stream[_Item_co](result.all_values())


_ResultValue = TypeVar('_ResultValue')
_StateValue = TypeVar('_StateValue', bound=AbstractStream)


@dataclass(frozen=True)
class UntilEmpty(processor.UnaryRule[_ResultValue, _StateValue]):
    '''applies child rule until stream is empty'''

    def __str__(self) -> str:
        return f'{self.child}!'

    def apply(
        self,
        state: processor.State[_ResultValue, _StateValue],
    ) -> processor.ResultAndState[_ResultValue, _StateValue]:
        child_results: MutableSequence[processor.Result[_ResultValue]] = []
        child_state = state
        while not child_state.value.empty:
            try:
                child_result_and_state = self.child.apply(child_state)
            except Error as error:
                raise processor.RuleError(rule=self, state=state,
                                          children=[error]) from error
            child_results.append(child_result_and_state.result)
            child_state = child_result_and_state.state
        return processor.ResultAndState(processor.Result(children=child_results), child_state)
