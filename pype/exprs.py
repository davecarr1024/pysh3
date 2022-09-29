'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from . import vals


class Error(Exception):
    '''exprs error'''


@dataclass(frozen=True)
class Result:
    '''result of evaluating an expression'''

    value: vals.Val
    is_return: bool = field(kw_only=True, default=False)


class Expr(ABC):  # pylint: disable=too-few-public-methods
    '''expr'''

    @abstractmethod
    def eval(self, scope: vals.Scope) -> Result:
        '''eval'''


@dataclass(frozen=True)
class Ref(Expr):
    '''ref'''

    name: str

    def __str__(self) -> str:
        return self.name

    def eval(self, scope: vals.Scope) -> Result:
        if self.name not in scope:
            raise Error(f'unknown ref {self}')
        return Result(scope[self.name])


@dataclass(frozen=True)
class Literal(Expr):
    '''literal'''

    value: vals.Val

    def __str__(self) -> str:
        return str(self.value)

    def eval(self, scope: vals.Scope) -> Result:
        return Result(self.value)


@dataclass(frozen=True)
class Assignment(Expr):
    '''assignment'''

    name: str
    value: Expr

    def __str__(self) -> str:
        return f'{self.name} = {self.value}'

    def eval(self, scope: vals.Scope) -> Result:
        value = self.value.eval(scope)
        scope[self.name] = value.value
        return value
