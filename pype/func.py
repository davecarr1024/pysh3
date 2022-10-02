'''vals'''

from dataclasses import dataclass

from pype import errors, params, builtins_, statements, vals, funcs


@dataclass(frozen=True)
class Func(funcs.AbstractFunc):
    '''func'''

    name: str
    _params: params.Params
    body: statements.Block

    @property
    def params(self) -> params.Params:
        return self._params

    def apply(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        try:
            func_scope = self._params.bind(scope, args)
        except errors.Error as error:
            raise errors.Error(
                f'failed to bind params for func {self} with args {args}: {error}') from error
        result = self.body.eval(func_scope)
        if result.return_ is not None and result.return_.value is not None:
            return result.return_.value
        return builtins_.none


@dataclass(frozen=True)
class Decl(statements.Decl):
    '''func decl'''

    _name: str
    params: params.Params
    body: statements.Block

    def str_(self, indent: int) -> str:
        return self.body.str_(indent, f'def {self.name}{self.params}')

    @property
    def name(self) -> str:
        return self._name

    def value(self, scope: vals.Scope) -> statements.Decl.Value:
        return Decl.Value(Func(self.name, self.params, self.body), statements.Result())
