'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Sequence, Sized
from pype import vals


class Error(Exception):
    '''exprs error'''


@dataclass(frozen=True)
class Arg:
    '''arg'''

    value: 'Expr'

    def eval(self, scope: vals.Scope) -> vals.Arg:
        '''eval'''
        return vals.Arg(self.value.eval(scope).value)


@dataclass(frozen=True)
class Args(Iterable[Arg], Sized):
    '''args'''

    _args: Sequence[Arg]

    def __len__(self) -> int:
        return len(self._args)

    def __iter__(self) -> Iterator[Arg]:
        return iter(self._args)

    def eval(self, scope: vals.Scope) -> vals.Args:
        '''evaluate the set of args in the given scope'''
        return vals.Args([arg.eval(scope) for arg in self._args])


@dataclass(frozen=True)
class Param:
    '''param'''

    name: str

    def bind(self, scope: vals.Scope, arg: vals.Arg) -> None:
        '''bind this param to the arg in the given scope'''
        scope[self.name] = arg.value


@dataclass(frozen=True)
class Params(Iterable[Param], Sized):
    '''params'''

    _params: Sequence[Param]

    def __len__(self) -> int:
        return len(self._params)

    def __iter__(self) -> Iterator[Param]:
        return iter(self._params)

    @property
    def tail(self) -> 'Params':
        '''return self without the first param'''
        if len(self._params) == 0:
            raise Error('empty params')
        return Params(self._params[1:])

    def bind(self, scope: vals.Scope, args: vals.Args) -> vals.Scope:
        '''bind the given args in a new scope'''
        if len(self) != len(args):
            raise Error(
                f'param mismatch: expected {len(self)} args but got {len(args)}')
        scope = scope.as_child()
        for param, arg in zip(self, args):
            param.bind(scope, arg)
        return scope


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


@dataclass(frozen=True)
class Namespace(Expr):
    '''namespace'''

    body: Sequence[Expr]

    def eval(self, scope: vals.Scope) -> Result:
        namespace_scope = scope.as_child()
        for expr in self.body:
            expr.eval(namespace_scope)
        return Result(value=vals.Namespace(namespace_scope))


@dataclass(frozen=True)
class Path(Expr):
    '''multipart path down object tree'''

    class Part(ABC):
        '''part of a path'''

        @abstractmethod
        def eval(self, scope: vals.Scope, object_: vals.Val) -> vals.Val:
            '''evaluate this part of the path'''

    @dataclass(frozen=True)
    class Member(Part):
        '''gets a member of an object'''

        name: str

        def eval(self, scope: vals.Scope, object_: vals.Val) -> vals.Val:
            if not self.name in object_:
                raise Error(f'unknown member {self.name} in object {object_}')
            return object_[self.name]

    @dataclass(frozen=True)
    class Call(Part):
        '''calls an object with args'''

        args: Args

        def eval(self, scope: vals.Scope, object_: vals.Val) -> vals.Val:
            return object_.apply(scope, self.args.eval(scope))

    root: Expr
    parts: Sequence[Part]

    def eval(self, scope: vals.Scope) -> Result:
        val = self.root.eval(scope).value
        for part in self.parts:
            val = part.eval(scope, val)
        return Result(val)


@dataclass(frozen=True)
class Class(Expr):
    '''class'''

    name: str
    body: Sequence[Expr]

    def eval(self, scope: vals.Scope) -> Result:
        members = scope.as_child()
        for expr in self.body:
            expr.eval(members)
        return Result(vals.Class(self.name, members))
