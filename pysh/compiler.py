'''exprs'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence
from . import runtime, types


class Error(Exception):
    '''base exprs error'''


class Expr(ABC):
    '''expression'''

    @abstractmethod
    def compile(self, scope: types.MutableScope) -> runtime.Expr:
        '''evaluate the type of this expr in the given types scope'''


@dataclass(frozen=True)
class Ref(Expr):
    '''ref'''

    value: str

    def __str__(self) -> str:
        return self.value

    def compile(self, scope: types.MutableScope) -> runtime.Expr:
        if self.value not in scope:
            raise Error(f'unknown var {self}')
        return runtime.Ref(scope[self.value], self.value)


@dataclass(frozen=True)
class Namespace(Expr):
    '''namespace'''

    name: Optional[str]
    children: Sequence[Expr]

    def compile(self, scope: types.MutableScope) -> types.Type:
        namespace_scope = scope.as_child()
        for child in self.children:
            child.compile(namespace_scope)
        namespace = types.Builtin.namespace(namespace_scope.vars)
        if self.name is not None:
            scope[self.name] = namespace
        return namespace


@dataclass(frozen=True)
class Decl(Expr):
    '''declaration'''

    type: Expr
    name: str
    value: Expr

    def compile(self, scope: types.MutableScope) -> types.Type:
        if self.name in scope:
            raise Error(f'redefining var {self.name}')
        type_ = self.type.compile(scope)
        value = self.value.compile(scope)
        if not type_.can_assign(value):
            raise Error(
                f'var {self.name} of type {type_} cannot be assigned val {value}')
        scope[self.name] = type_
        return type_

    def eval(self, scope: runtime.MutableScope) -> runtime.Val:
        if self.name in scope:
            raise Error(f'redefining var {self.name}')
        type_ = self.type.eval(scope)
        value = self.value.eval(scope)
        if not isinstance(type_, runtime.Class):
            raise Error(f'decl type {type_} must be a class')
        scope[self.name] = runtime.Var(type_, value)
        return value
