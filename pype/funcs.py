'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Iterator, MutableSequence, Sequence
from pype import vals


class Error(Exception):
    '''funcs error'''


@dataclass(frozen=True)
class Param:
    '''param'''

    name: str


@dataclass(frozen=True)
class Params(Iterable[Param]):
    '''params'''

    params: Sequence[Param]

    def __len__(self) -> int:
        return len(self.params)

    def __iter__(self) -> Iterator[Param]:
        return iter(self.params)

    @property
    def tail(self) -> 'Params':
        '''return self without the first param'''
        if len(self.params) == 0:
            raise Error('empty params')
        return Params(self.params[1:])

    def bind(self, scope: vals.Scope, args: Sequence[vals.Val]) -> vals.Scope:
        '''bind the given args in a new scope'''
        if len(self.params) != len(args):
            raise Error(
                f'param mismatch: expected {len(self.params)} args got {len(args)}')
        return scope.as_child(**{param.name: arg for param, arg in zip(self.params, args)})


class AbstractFunc(vals.Val, ABC):
    '''func interface'''

    @property
    @abstractmethod
    def params(self) -> Params:
        '''params'''

    @abstractmethod
    def apply(self, scope: vals.Scope, args: Sequence[vals.Val]) -> vals.Val:
        ...


@dataclass(frozen=True)
class BindableFunc(AbstractFunc):
    '''bindable func'''

    func: AbstractFunc

    def __post_init__(self):
        if len(self.func.params) == 0:
            raise Error(
                f'unable to create bindable func from func {self.func} with 0 params')

    @property
    def params(self) -> Params:
        return self.func.params

    def apply(self, scope: vals.Scope, args: Sequence[vals.Val]) -> vals.Val:
        return self.func.apply(scope, args)

    @property
    def can_bind(self) -> bool:
        return True

    def bind(self, object_: vals.Val) -> vals.Val:
        return BoundFunc(object_, self)


@dataclass(frozen=True)
class BoundFunc(AbstractFunc):
    '''bound func'''

    object_: vals.Val
    func: BindableFunc

    def __post_init__(self):
        if len(self.func.params) == 0:
            raise Error(f'unable to bind func {self.func} with 0 params')

    @property
    def params(self) -> Params:
        return self.func.params.tail

    def apply(self, scope: vals.Scope, args: Sequence[vals.Val]) -> vals.Val:
        bound_args: MutableSequence[vals.Val] = [self.object_]
        bound_args.extend(args)
        return self.func.apply(scope, bound_args)
