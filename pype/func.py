'''vals'''

from dataclasses import dataclass
from typing import Optional, Sequence
from . import vals, exprs, builtins_, funcs


@dataclass(frozen=True)
class Return(exprs.Expr):
    '''return statement'''

    value: Optional[exprs.Expr]

    def __str__(self) -> str:
        return f'return {self.value}'

    def eval(self, scope: vals.Scope) -> exprs.Result:
        if self.value is None:
            return exprs.Result(builtins_.none, is_return=True)
        return exprs.Result(self.value.eval(scope).value, is_return=True)


@dataclass(frozen=True)
class Func(funcs.AbstractFunc):
    '''func'''

    body: Sequence[exprs.Expr]
    _params: Sequence[str]

    @property
    def params(self) -> Sequence[str]:
        return self._params

    def apply(self, scope: vals.Scope, args: Sequence[vals.Val]) -> vals.Val:
        '''apply'''
        if len(self.params) != len(args):
            raise funcs.Error(
                f'arg count mismatch for {self}: expected {len(self.params)} got {len(args)}')
        func_scope = scope.as_child(**dict(zip(self.params, args)))
        for expr in self.body:
            result = expr.eval(func_scope)
            if result.is_return:
                return result.value
        return builtins_.none
