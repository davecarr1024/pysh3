'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pype import vals, exprs


class Error(Exception):
    '''funcs error'''


class AbstractFunc(vals.Val, ABC):
    '''func interface'''

    @property
    @abstractmethod
    def params(self) -> exprs.Params:
        '''params'''

    @abstractmethod
    def apply(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
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
    def params(self) -> exprs.Params:
        return self.func.params

    def apply(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
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
    def params(self) -> exprs.Params:
        return self.func.params.tail

    def apply(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        return self.func.apply(scope, args.prepend(vals.Arg(self.object_)))
