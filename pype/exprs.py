'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Iterator, Sequence, Sized
from pype import errors, vals


@dataclass(frozen=True)
class Arg:
    '''arg'''

    value: 'Expr'

    def eval(self, scope: vals.Scope) -> vals.Arg:
        '''eval'''
        return vals.Arg(self.value.eval(scope))


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


class Expr(ABC):  # pylint: disable=too-few-public-methods
    '''expr'''

    @abstractmethod
    def eval(self, scope: vals.Scope) -> vals.Val:
        '''eval'''


@dataclass(frozen=True)
class Ref(Expr):
    '''ref'''

    name: str

    def __str__(self) -> str:
        return self.name

    def eval(self, scope: vals.Scope) -> vals.Val:
        if self.name not in scope:
            raise errors.Error(f'unknown ref {self}')
        return scope[self.name]


@dataclass(frozen=True)
class Literal(Expr):
    '''literal'''

    value: vals.Val

    def __str__(self) -> str:
        return str(self.value)

    def eval(self, scope: vals.Scope) -> vals.Val:
        return self.value


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
                raise errors.Error(
                    f'unknown member {self.name} in object {object_}')
            return object_[self.name]

    @dataclass(frozen=True)
    class Call(Part):
        '''calls an object with args'''

        args: Args

        def eval(self, scope: vals.Scope, object_: vals.Val) -> vals.Val:
            return object_.apply(scope, self.args.eval(scope))

    root: Expr
    parts: Sequence[Part]

    def __str__(self) -> str:
        return str(self.root) + ''.join(str(part) for part in self.parts)

    def eval(self, scope: vals.Scope) -> vals.Val:
        object_ = self.root.eval(scope)
        for part in self.parts:
            object_ = part.eval(scope, object_)
        return object_


@dataclass(frozen=True)
class BinaryOperation(Expr):
    '''binary operation'''

    class Operator(Enum):
        ADD = '+'
        SUB = '-'
        MUL = '*'
        DIV = '/'
        AND = 'and'
        OR = 'or'

    operator: Operator
    lhs: Expr
    rhs: Expr

    def __str__(self) -> str:
        return f'{self.lhs} {self.operator.value} {self.rhs}'

    @staticmethod
    def _func_for_operator(operator: 'BinaryOperation.Operator') -> str:
        return f'__{operator.name.lower()}__'

    def eval(self, scope: vals.Scope) -> vals.Val:
        lhs = self.lhs.eval(scope)
        rhs = self.rhs.eval(scope)
        func = lhs[self._func_for_operator(self.operator)]
        return func.apply(scope, vals.Args([vals.Arg(rhs)]))
