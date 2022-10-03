'''builtins'''

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import operator
from typing import Callable, Generic, Iterator, Mapping,  Type, TypeVar

from pype import errors, funcs, params, vals


@dataclass(frozen=True)
class Arg:
    '''arg'''

    name: str
    value: vals.Val


@dataclass(frozen=True)
class Args(Mapping[str, Arg]):
    '''args'''

    _args: Mapping[str, Arg]

    @staticmethod
    def for_params_and_args(params_: params.Params, args: vals.Args) -> 'Args':
        if len(params_) != len(args):
            raise errors.Error(
                f'param count {len(params_)} != args count {len(args)}')
        return Args({param.name: Arg(param.name, arg.value) for param, arg in zip(params_, args)})

    def __getitem__(self, name: str) -> Arg:
        return self._args[name]

    def __iter__(self) -> Iterator[str]:
        return iter(self._args)

    def __len__(self) -> int:
        return len(self._args)


class _Func(funcs.AbstractFunc, ABC):
    '''builtin func'''

    @abstractmethod
    def apply_builtin(self, scope: vals.Scope, args: Args) -> vals.Val:
        '''builtin func logic'''

    def apply(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        '''apply'''
        return self.apply_builtin(scope, Args.for_params_and_args(self.params, args))


@dataclass(frozen=True)
class Class(vals.AbstractClass):
    '''builtin class'''

    _name: str
    _members: vals.Scope
    __object_type: Type['_Object']

    @property
    def name(self) -> str:
        return self._name

    @property
    def members(self) -> vals.Scope:
        return self._members

    @property
    def _object_type(self) -> Type['_Object']:
        return self.__object_type


@dataclass(frozen=True)
class _Object(vals.Object):
    '''generic builtin object'''

    # don't waste time deep comparing builtin objects
    class_: vals.AbstractClass = field(compare=False, repr=False)
    _members: vals.Scope = field(compare=False, repr=False)


_Value = TypeVar('_Value')


@dataclass(frozen=True)
class _ValueObject(_Object, Generic[_Value]):
    value: _Value


@dataclass(frozen=True)
class IntObject(_ValueObject[int]):
    '''int builtin'''


@dataclass(frozen=True)
class _IntFunc(_Func, ABC):
    name: str
    func: Callable[[int, int], int]

    @property
    def params(self) -> params.Params:
        return params.Params([params.Param('self'), params.Param('rhs')])

    @staticmethod
    def _int_arg(arg: Arg) -> IntObject:
        if not isinstance(arg.value, IntObject):
            raise errors.Error(f'invalid int func arg {arg}')
        return arg.value

    def apply_builtin(self, scope: vals.Scope, args: Args) -> vals.Val:
        self_ = self._int_arg(args['self']).value
        rhs = self._int_arg(args['rhs']).value
        return int_(self.func(self_, rhs))


IntClass = Class(
    'int',
    vals.Scope({
        '__add__': funcs.BindableFunc(_IntFunc('__add__', operator.add)),
        '__sub__': funcs.BindableFunc(_IntFunc('__sub__', operator.sub)),
        '__mul__': funcs.BindableFunc(_IntFunc('__mul__', operator.mul)),
        '__div__': funcs.BindableFunc(_IntFunc('__div__', operator.floordiv)),
    }),
    IntObject,
)


def int_(value: int) -> vals.Object:
    return IntClass.instantiate(value)


@dataclass(frozen=True)
class FloatObject(_ValueObject[float]):
    '''float builtin'''


@dataclass(frozen=True)
class _FloatFunc(_Func, ABC):
    name: str
    func: Callable[[float, float], float]

    @property
    def params(self) -> params.Params:
        return params.Params([params.Param('self'), params.Param('rhs')])

    @staticmethod
    def _float_arg(arg: Arg) -> FloatObject:
        if not isinstance(arg.value, FloatObject):
            raise errors.Error(f'invalid float func arg {arg}')
        return arg.value

    def apply_builtin(self, scope: vals.Scope, args: Args) -> vals.Val:
        self_ = self._float_arg(args['self']).value
        rhs = self._float_arg(args['rhs']).value
        return float_(self.func(self_, rhs))


FloatClass = Class(
    'float',
    vals.Scope({
        '__add__': funcs.BindableFunc(_FloatFunc('__add__', operator.add)),
        '__sub__': funcs.BindableFunc(_FloatFunc('__sub__', operator.sub)),
        '__mul__': funcs.BindableFunc(_FloatFunc('__mul__', operator.mul)),
        '__div__': funcs.BindableFunc(_FloatFunc('__div__', operator.truediv)),
    }),
    FloatObject,
)


def float_(value: float) -> vals.Object:
    return FloatClass.instantiate(value)


@dataclass(frozen=True)
class StrObject(_ValueObject[str]):
    '''str builtin'''


@dataclass(frozen=True)
class _StrFunc(_Func, ABC):
    name: str
    func: Callable[[str, str], str]

    @property
    def params(self) -> params.Params:
        return params.Params([params.Param('self'), params.Param('rhs')])

    @staticmethod
    def _str_arg(arg: Arg) -> StrObject:
        if not isinstance(arg.value, StrObject):
            raise errors.Error(f'invalid str func arg {arg}')
        return arg.value

    def apply_builtin(self, scope: vals.Scope, args: Args) -> vals.Val:
        self_ = self._str_arg(args['self']).value
        rhs = self._str_arg(args['rhs']).value
        return str_(self.func(self_, rhs))


StrClass = Class(
    'str',
    vals.Scope({
        '__add__': funcs.BindableFunc(_StrFunc('__add__', operator.add)),
    }),
    StrObject,
)


def str_(value: str) -> vals.Object:
    return StrClass.instantiate(value)


@dataclass(frozen=True)
class BoolObject(_ValueObject[bool]):
    '''bool builtin'''


@dataclass(frozen=True)
class _BoolFunc(_Func, ABC):
    name: str
    func: Callable[[bool, bool], bool]

    @property
    def params(self) -> params.Params:
        return params.Params([params.Param('self'), params.Param('rhs')])

    @staticmethod
    def _bool_arg(arg: Arg) -> BoolObject:
        if not isinstance(arg.value, BoolObject):
            raise errors.Error(f'invalid bool func arg {arg}')
        return arg.value

    def apply_builtin(self, scope: vals.Scope, args: Args) -> vals.Val:
        self_ = self._bool_arg(args['self']).value
        rhs = self._bool_arg(args['rhs']).value
        return bool_(self.func(self_, rhs))


BoolClass = Class(
    'bool',
    vals.Scope({
        '__and__': funcs.BindableFunc(_BoolFunc('__and__', operator.and_)),
        '__or__': funcs.BindableFunc(_BoolFunc('__or__', operator.or_)),
    }),
    BoolObject,
)


def bool_(value: bool) -> vals.Object:
    return BoolClass.instantiate(value)


true = bool_(True)
false = bool_(False)


class NoneObject(_Object):
    '''none builtin'''


NoneClass = Class(
    'NoneType',
    vals.Scope({}),
    NoneObject,
)

none = NoneClass.instantiate()
