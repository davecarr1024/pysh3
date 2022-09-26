'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping
from . import scopes, types


class Error(Exception):
    '''generic vals error'''


class Val(ABC):
    '''val'''

    @property
    @abstractmethod
    def type(self) -> types.Type:
        '''the type of this val'''


class Class(Val, types.Type):
    '''a class is a val that defines a type'''


@dataclass(frozen=True)
class Object(Val):
    '''instance of a class'''

    class_: Class

    @property
    def type(self) -> types.Type:
        return self.class_


@dataclass(frozen=True)
class BuiltinClass(Class):
    '''builtin class'''

    _type: types.Builtin

    @property
    def type(self) -> types.Type:
        return types.Builtin('builtin', {})

    @property
    def name(self) -> str:
        return self._type.name

    @property
    def members(self) -> Mapping[str, types.Type]:
        return self._type.members

    def can_assign(self, rhs: types.Type) -> bool:
        return self._type.can_assign(rhs)

    @staticmethod
    def int() -> 'BuiltinClass':
        '''int'''
        return BuiltinClass(types.Builtin.int())


@dataclass
class Var:
    '''a variable with a type and a value'''

    type: types.Type
    _val: Val

    def can_assign(self, val: Val) -> bool:
        '''can this var be assigned with the given val'''
        return self.type.can_assign(val.type)

    @property
    def val(self) -> Val:
        '''the value held by this var'''
        return self._val

    @val.setter
    def set_val(self, val: Val) -> None:
        if not self.can_assign(val):
            raise Error(f'var {self} cannot be set with val {val}')
        self._val = val

    @staticmethod
    def for_val(val: Val) -> 'Var':
        '''create a var for this val with its type'''
        return Var(val.type, val)


Scope = scopes.Scope[Var]
MutableScope = scopes.MutableScope[Var]


class Expr(ABC):
    '''expr'''

    @property
    @abstractmethod
    def type(self) -> types.Type:
        '''type'''

    @abstractmethod
    def eval(self, scope: MutableScope) -> Val:
        '''evaluate the value of this expr in the given scope'''


@dataclass(frozen=True)
class Ref(Expr):
    '''ref'''

    _type: types.Type
    value: str

    def __str__(self) -> str:
        return self.value

    @property
    def type(self) -> types.Type:
        return self._type

    def eval(self, scope: MutableScope) -> Val:
        if self.value not in scope:
            raise Error(f'unknown ref {self}')
        val = scope[self.value].val
        if not self.type.can_assign(val.type):
            raise Error(f'{self} has invalid val {val}')
        return val


def default_scope() -> MutableScope:
    '''the default vals scope'''
    return MutableScope(None, {
        'int': Var.for_val(BuiltinClass.int()),
    })
