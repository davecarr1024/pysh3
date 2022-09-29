'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Iterator,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Type,
)


class Error(Exception):
    '''vals error'''


class Val(ABC):
    '''val'''

    def apply(self, scope: 'Scope', args: Sequence['Val']) -> 'Val':
        '''apply'''
        raise Error(f'applying uncallable val {self}')

    @property
    def members(self) -> 'Scope':
        '''members'''
        return Scope()

    @property
    def can_bind(self) -> bool:
        '''can this val be bound to an instance'''
        return False

    def bind(self, object_: 'Val') -> 'Val':
        '''bind'''
        raise Error(f'binding unbindable val {self}')

    def __contains__(self, name: str) -> bool:
        return name in self.members

    def __getitem__(self, name: str) -> 'Val':
        if name not in self.members:
            raise Error(f'unknown member {name} in {self}')
        return self.members[name]


@dataclass(frozen=True)
class Scope:
    '''scope'''

    parent: Optional['Scope'] = None
    _vals: MutableMapping[str, Val] = field(
        default_factory=dict[str, Val])

    def __iter__(self) -> Iterator[str]:
        return iter(self._vals)

    def __contains__(self, name: str) -> bool:
        return name in self._vals or (self.parent is not None and name in self.parent)

    def __getitem__(self, name: str) -> Val:
        if name in self._vals:
            return self._vals[name]
        if self.parent is not None:
            return self.parent[name]
        raise Error(f'unknown var {name}')

    def __setitem__(self, name: str, val: Val) -> None:
        self._vals[name] = val

    @property
    def vals(self) -> Mapping[str, Val]:
        '''vals'''
        return self._vals

    @property
    def all_vals(self) -> Mapping[str, Val]:
        '''all vals contained in this scope and its parents'''
        vals: MutableMapping[str, Val] = {}
        if self.parent:
            vals.update(self.parent.all_vals)
        vals.update(self.vals)
        return vals

    def as_child(self, **vals: Val) -> 'Scope':
        '''nest this scope inside a new scope'''
        return Scope(self, vals)

    def bind_vals(self, object_: Val) -> 'Mapping[str,Val]':
        '''get all this scope's vals bound to object_'''
        return {
            name: val.bind(object_)
            for name, val in self.all_vals.items()
            if val.can_bind
        }

    def bind(self, object_: Val) -> 'Scope':
        '''return a new child scope with all bindable vals in this scope bound to object_'''
        return Scope(self, dict[str, Val](self.bind_vals(object_)))

    def bind_self(self, object_: Val) -> None:
        '''bind this scope to the given object'''
        self._vals.update(self.bind_vals(object_))

    @staticmethod
    def default() -> 'Scope':
        '''default scope'''
        return Scope()


@dataclass(frozen=True)
class Namespace(Val):
    '''namespace'''

    _members: Scope

    @property
    def members(self) -> Scope:
        return self._members


class AbstractClass(Val, ABC):
    '''abstract class'''

    @property
    @abstractmethod
    def name(self) -> str:
        '''name of this class'''

    @property
    @abstractmethod
    def members(self) -> Scope:
        ...

    @property
    def _object_type(self) -> Type['Object']:
        return Object

    def apply(self, scope: Scope, args: Sequence[Val]) -> 'Object':
        object_ = self._object_type(self, self.members.as_child())
        if '__init__' in object_:
            object_['__init__'].apply(scope, args)
        return object_


@dataclass(frozen=True)
class Class(AbstractClass):
    '''class'''

    _name: str
    _members: Scope

    @property
    def name(self) -> str:
        return self._name

    @property
    def members(self) -> Scope:
        return self._members


@dataclass(frozen=True)
class Object(Val):
    '''object'''

    class_: AbstractClass
    _members: Scope

    def __post_init__(self):
        self._members.bind_self(self)

    @property
    def members(self) -> Scope:
        return self._members

    def apply(self, scope: Scope, args: Sequence[Val]) -> Val:
        if '__call__' not in self:
            raise Error(f'object {self} not callable')
        return self['__call__'].apply(scope, args)
