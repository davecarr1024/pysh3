'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
import inspect
from typing import (
    Callable,
    MutableSequence,
    Sequence,
)
from . import vals, exprs


class Error(Exception):
    '''funcs error'''


class AbstractFunc(vals.Val, ABC):
    '''func interface'''

    @property
    @abstractmethod
    def params(self) -> Sequence[str]:
        '''params'''


@dataclass(frozen=True)
class Func(AbstractFunc):
    '''func'''

    body: Sequence[exprs.Expr]
    _params: Sequence[str]

    @property
    def params(self) -> Sequence[str]:
        return self._params

    def apply(self, scope: vals.Scope, args: Sequence[vals.Val]) -> vals.Val:
        '''apply'''
        if len(self.params) != len(args):
            raise Error(
                f'arg count mismatch for {self}: expected {len(self.params)} got {len(args)}')
        func_scope = scope.as_child(**dict(zip(self.params, args)))
        for expr in self.body:
            result = expr.eval(func_scope)
            if result.is_return:
                return result.value
        return vals.none


@dataclass(frozen=True)
class BindableFunc(AbstractFunc):
    '''bindable func'''

    func: Func

    def __post_init__(self):
        if len(self.func.params) == 0:
            raise Error(
                f'unable to create bindable func from func {self.func} with 0 params')

    @property
    def params(self) -> Sequence[str]:
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
    def params(self) -> Sequence[str]:
        return self.func.params[1:]

    def apply(self, scope: vals.Scope, args: Sequence[vals.Val]) -> vals.Val:
        bound_args: MutableSequence[vals.Val] = [self.object_]
        bound_args.extend(args)
        return self.func.apply(scope, bound_args)


@dataclass(frozen=True)
class BuiltinFunc(AbstractFunc):
    '''builtin func'''

    func: Callable[[vals.Scope, Sequence[vals.Val]], vals.Val]

    @property
    def params(self) -> Sequence[str]:
        raise NotImplementedError(inspect.getfullargspec(self.func))

    def apply(self, scope: vals.Scope, args: Sequence[vals.Val]) -> vals.Val:
        return self.func(scope, args)
