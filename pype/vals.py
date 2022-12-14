'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Sized,
    Type,
)

from pype import errors


@dataclass(frozen=True)
class Arg:
    '''arg'''

    value: 'Val'


@dataclass(frozen=True)
class Args(Iterable[Arg], Sized):  # pylint: disable=duplicate-code
    '''args'''

    _args: Sequence[Arg]

    def __len__(self) -> int:
        return len(self._args)

    def __iter__(self) -> Iterator[Arg]:
        return iter(self._args)

    def prepend(self, arg: Arg) -> 'Args':
        '''prepend the given arg to these args'''
        return Args([arg] + list(self._args))


class Val(ABC, Mapping[str, 'Val']):
    '''val'''

    def apply(self, scope: 'Scope', args: Args) -> 'Val':
        '''apply'''
        raise errors.Error(f'applying uncallable val {self}')

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
        raise errors.Error(f'binding unbindable val {self}')

    def __contains__(self, name: object) -> bool:
        return name in self.members

    def __len__(self) -> int:
        return len(self.members)

    def __iter__(self) -> Iterator[str]:
        return iter(self.members)

    def __getitem__(self, name: str) -> 'Val':
        if name not in self.members:
            raise errors.Error(f'unknown member {name} in {self}')
        return self.members[name]


@dataclass(frozen=True)
class Scope(MutableMapping[str, Val]):
    '''scope'''

    parent: Optional['Scope'] = field(
        default=None, compare=False, kw_only=True)
    _vals: MutableMapping[str, Val] = field(
        default_factory=dict[str, Val])

    def __post_init__(self):
        descendents: MutableSequence[Scope] = list[Scope]((self,))
        scope = self
        while scope.parent is not None:
            scope = scope.parent
            assert all(scope is not descendent for descendent in descendents)
            descendents.append(scope)

    def __repr__(self) -> str:
        return repr(self._vals)

    def __iter__(self) -> Iterator[str]:
        return iter(self._vals)

    def __contains__(self, name: object) -> bool:
        return (isinstance(name, str)
                and (name in self._vals
                     or (self.parent is not None and name in self.parent)))

    def __getitem__(self, name: str) -> Val:
        if name in self._vals:
            return self._vals[name]
        if self.parent is not None:
            return self.parent[name]
        raise errors.Error(f'unknown var {name}')

    def __setitem__(self, name: str, val: Val) -> None:
        self._vals[name] = val

    def __delitem__(self, name: str) -> None:
        del self._vals[name]

    def __len__(self) -> int:
        return len(self._vals)

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
        return Scope(vals, parent=self)

    def bind_vals(self, object_: Val) -> 'Mapping[str,Val]':
        '''get all this scope's vals bound to object_'''
        return {
            name: val.bind(object_)
            for name, val in self.all_vals.items()
            if val.can_bind
        }

    def bind(self, object_: Val) -> 'Scope':
        '''return a new child scope with all bindable vals in this scope bound to object_'''
        return Scope(dict[str, Val](self.bind_vals(object_)), parent=self)

    def bind_self(self, object_: Val) -> None:
        '''bind this scope to the given object'''
        self._vals.update(self.bind_vals(object_))


@dataclass(frozen=True)
class Namespace(Val):
    '''namespace'''

    name: Optional[str] = field(kw_only=True, default=None)
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

    def instantiate(self, *args: Any, **kwargs: Any) -> 'Object':
        object_ = self._object_type(
            self, self.members.as_child(), *args, **kwargs)
        object_.bind_self()
        return object_

    def apply(self, scope: Scope, args: Args) -> 'Object':
        object_ = self.instantiate()
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
class Object(Val, ABC):
    '''object'''

    class_: AbstractClass
    _members: Scope

    def bind_self(self) -> None:
        '''bind this object's scope to itself

        Note that this must be called after construction of an object before it can be used.
        '''
        self._members.bind_self(self)

    @property
    def members(self) -> Scope:
        '''members'''
        return self._members

    def apply(self, scope: Scope, args: Args) -> Val:
        if '__call__' not in self:
            raise errors.Error(f'object {self} not callable')
        return self['__call__'].apply(scope, args)
