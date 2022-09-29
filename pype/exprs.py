'''vals'''

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence
from ..core import loader, parser
from . import vals


class Error(Exception):
    '''exprs error'''


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

    @classmethod
    @abstractmethod
    def load_result(cls, result: parser.Result) -> 'Expr':
        '''load this expr type from parser result'''
        return loader.factory({
            'ref': Ref.load_result,
        })(result)

    @staticmethod
    def load(input_str: str) -> 'Expr':
        '''load an expr from a string'''
        parser_ = loader.load_parser(r'''
        _ws = "\w+";
        id = "[_a-zA-Z][_a-zA-Z0-9]*";
        int = "[1-9][0-9]*";

        root => line+;
        line => expr ";";
        expr => ref;
        ref => id;
        ''')
        result = parser_.apply(input_str)
        return Namespace.load_result(result)


@ dataclass(frozen=True)
class Ref(Expr):
    '''ref'''

    name: str

    def __str__(self) -> str:
        return self.name

    def eval(self, scope: vals.Scope) -> Result:
        if self.name not in scope:
            raise Error(f'unknown ref {self}')
        return Result(scope[self.name])

    @ classmethod
    def load_result(cls, result: parser.Result) -> Expr:
        return Ref(loader.get_token_value(result))


@ dataclass(frozen=True)
class Literal(Expr):
    '''literal'''

    value: vals.Val

    def __str__(self) -> str:
        return str(self.value)

    def eval(self, scope: vals.Scope) -> Result:
        return Result(self.value)

    @ classmethod
    def load_result(cls, result: parser.Result) -> Expr:
        raise NotImplementedError(result)


@ dataclass(frozen=True)
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

    @ classmethod
    def load_result(cls, result: parser.Result) -> Expr:
        raise NotImplementedError(result)


@ dataclass(frozen=True)
class Namespace(Expr):
    '''namespace'''

    body: Sequence[Expr]

    def eval(self, scope: vals.Scope) -> Result:
        namespace_scope = scope.as_child()
        for expr in self.body:
            expr.eval(namespace_scope)
        return Result(value=vals.Namespace(namespace_scope))

    @ classmethod
    def load_result(cls, result: parser.Result) -> Expr:
        return Namespace([Expr.load_result(expr) for expr in result['expr']])
