'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Sequence, Sized, final
from pype import exprs, vals


@dataclass(frozen=True)
class Result:
    '''result of evaluating a statement'''

    @dataclass(frozen=True)
    class Return:
        '''return'''

        value: Optional[vals.Val]

    return_: Optional[Return] = field(kw_only=True, default=None)


class Statement(ABC):
    '''statement'''

    def __str__(self) -> str:
        return self.str_(0)

    def str_(self, indent: int) -> str:
        return self._str_prefix(indent, self._str_line())

    def _str_line(self) -> str:
        '''strify this statement into one line'''
        return repr(self)

    @final
    def _str_prefix(self, indent: int, val: str = '') -> str:
        return f'\n{"  "*indent}{val}'

    @abstractmethod
    def eval(self, scope: vals.Scope) -> Result:
        '''eval'''


@dataclass(frozen=True)
class Block(Iterable[Statement], Sized, ABC):
    '''block of statements'''

    _statements: Sequence[Statement]

    def __str__(self) -> str:
        return self.str_(0, '')

    def __len__(self) -> int:
        return len(self._statements)

    def __iter__(self) -> Iterator[Statement]:
        return iter(self._statements)

    def str_(self, indent: int, header: str) -> str:
        output = '  '*indent
        output += ' '.join((header, '{'))
        for statement in self._statements:
            output += statement.str_(indent+1)
        output += f'\n{"  "*indent}}}'
        return output

    def eval(self, scope: vals.Scope) -> Result:
        for statement in self._statements:
            result = statement.eval(scope)
            if result.return_ is not None:
                return result
        return Result()


@dataclass(frozen=True)
class Assignment(Statement):
    '''assignment'''

    name: str
    value: exprs.Expr

    def _str_line(self) -> str:
        return f'{self.name} = {self.value};'

    def eval(self, scope: vals.Scope) -> Result:
        scope[self.name] = self.value.eval(scope)
        return Result()


@dataclass(frozen=True)
class ExprStatement(Statement):
    '''a statement that only contains an expr'''

    value: exprs.Expr

    def _str_line(self) -> str:
        return f'{self.value};'

    def eval(self, scope: vals.Scope) -> Result:
        self.value.eval(scope)
        return Result()


@dataclass(frozen=True)
class Return(Statement):
    '''return statement'''

    value: Optional[exprs.Expr]

    def _str_line(self) -> str:
        if self.value:
            return f'return {self.value};'
        return 'return;'

    def eval(self, scope: vals.Scope) -> Result:
        if self.value:
            return Result(return_=Result.Return(self.value.eval(scope)))
        return Result(return_=Result.Return(None))


@dataclass(frozen=True)
class Decl(Statement):
    '''declaration'''

    @dataclass(frozen=True)
    class Value:
        '''result of evaluating decl value'''

        value: vals.Val
        result: Result

    @property
    @abstractmethod
    def name(self) -> Optional[str]:
        '''name'''

    @abstractmethod
    def value(self, scope: vals.Scope) -> Value:
        '''value'''

    @final
    def eval(self, scope: vals.Scope) -> Result:
        value = self.value(scope)
        if self.name is not None:
            scope[self.name] = value.value
        return value.result


@dataclass(frozen=True)
class Class(Decl):
    '''class'''

    _name: str
    body: Block

    def str_(self, indent: int) -> str:
        return self.body.str_(indent, f'class {self.name}')

    @property
    def name(self) -> str:
        return self._name

    def value(self, scope: vals.Scope) -> Decl.Value:
        members = scope.as_child()
        result = self.body.eval(members)
        return Decl.Value(vals.Class(self.name, members), result)


@dataclass(frozen=True)
class Namespace(Decl):
    '''namespace'''

    _name: Optional[str] = field(kw_only=True, default=None)
    body: Block

    def str_(self, indent: int) -> str:
        return self.body.str_(indent, f'namespace {self.name}')

    @property
    def name(self) -> Optional[str]:
        return self._name

    def value(self, scope: vals.Scope) -> Decl.Value:
        members = scope.as_child()
        result = self.body.eval(members)
        return Decl.Value(vals.Namespace(members, name=self.name), result)

