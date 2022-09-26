'''scope'''

from dataclasses import dataclass, field
from typing import Generic, Mapping, MutableMapping, Optional, TypeVar


class Error(Exception):
    '''generic scope error'''


_Var = TypeVar('_Var')


@dataclass(frozen=True)
class Scope(Generic[_Var]):
    '''scope'''

    _parent: Optional['Scope[_Var]'] = None

    _vars: MutableMapping[str, _Var] = field(
        default_factory=dict[str, _Var])

    def __contains__(self, key: str) -> bool:
        return key in self._vars or (self._parent is not None and key in self._parent)

    def __getitem__(self, key: str) -> _Var:
        if key in self._vars:
            return self._vars[key]
        if self._parent is not None:
            return self._parent[key]
        raise Error(f'unknown var {key}')

    @property
    def vars(self) -> Mapping[str, _Var]:
        '''vals'''
        return self._vars

    def as_child(self) -> 'Scope[_Var]':
        '''nest this scope in a new scope'''
        return Scope[_Var](_parent=self)


@dataclass(frozen=True)
class MutableScope(Scope[_Var]):
    '''mutable scope'''

    def __setitem__(self, key: str, val: _Var):
        self._vars[key] = val

    def as_child(self) -> 'MutableScope[_Var]':
        raise NotImplementedError()
