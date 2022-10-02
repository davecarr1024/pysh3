from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence, Sized
from pype import errors, vals


@dataclass(frozen=True)
class Param:
    '''param'''

    name: str

    def __str__(self) -> str:
        return self.name

    def bind(self, scope: vals.Scope, arg: vals.Arg) -> None:
        '''bind this param to the arg in the given scope'''
        scope[self.name] = arg.value


@dataclass(frozen=True)
class Params(Iterable[Param], Sized):
    '''params'''

    _params: Sequence[Param]

    def __str__(self) -> str:
        return '(' + ', '.join(str(param) for param in self._params) + ')'

    def __len__(self) -> int:
        return len(self._params)

    def __iter__(self) -> Iterator[Param]:
        return iter(self._params)

    @property
    def tail(self) -> 'Params':
        '''return self without the first param'''
        if len(self._params) == 0:
            raise errors.Error('empty params')
        return Params(self._params[1:])

    def bind(self, scope: vals.Scope, args: vals.Args) -> vals.Scope:
        '''bind the given args in a new scope'''
        if len(self) != len(args):
            raise errors.Error(
                f'param mismatch: expected {len(self)} args but got {len(args)}')
        scope = scope.as_child()
        for param, arg in zip(self, args):
            param.bind(scope, arg)
        return scope
