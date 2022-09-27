'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from . import vals


class Error(Exception):
    '''exprs error'''


@dataclass(frozen=True)
class Result:
    '''result of evaluating an expression'''

    value: vals.Val
    is_return: bool = False


class Expr(ABC):
    '''expr'''

    @abstractmethod
    def eval(self, scope: vals.Scope) -> Result:
        '''eval'''


@dataclass(frozen=True)
class ReturnStatement(Expr):
    '''return statement'''

    value: Expr

    def eval(self, scope: vals.Scope) -> Result:
        return self.value.eval(scope)


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


@dataclass(frozen=True)
class Return(Expr):
    '''return statement'''

    value: Expr

    def __str__(self) -> str:
        return f'return {self.value}'

    def eval(self, scope: vals.Scope) -> Result:
        return Result(self.value.eval(scope).value, is_return=True)
