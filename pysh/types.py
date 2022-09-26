'''types'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping
from . import scopes


class Type(ABC):
    '''type'''

    @property
    @abstractmethod
    def name(self) -> str:
        '''name of this type'''

    @property
    @abstractmethod
    def members(self) -> Mapping[str, 'Type']:
        '''members of this type'''

    @abstractmethod
    def can_assign(self, rhs: 'Type') -> bool:
        '''can this type be assigned to by rhs'''


Scope = scopes.Scope[Type]
MutableScope = scopes.MutableScope[Type]


@dataclass(frozen=True)
class Builtin(Type):
    '''builtin type'''

    _name: str
    _members: Mapping[str, Type]

    @property
    def name(self) -> str:
        return self._name

    @property
    def members(self) -> Mapping[str, Type]:
        return self._members

    def can_assign(self, rhs: Type) -> bool:
        return rhs == self

    @staticmethod
    def int() -> 'Builtin':
        '''int'''
        return Builtin('int', {})

    @staticmethod
    def namespace(members: Mapping[str, Type]) -> 'Builtin':
        '''namespace'''
        return Builtin('namespace', members)


def default_scope() -> MutableScope:
    '''the default types scope'''
    return MutableScope(None, {
        'int': Builtin.int(),
    })
