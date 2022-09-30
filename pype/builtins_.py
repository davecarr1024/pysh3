'''builtins'''

from dataclasses import dataclass, field
from functools import cache
import inspect
from typing import Callable, Generic, Optional, Type, TypeVar

from pype import exprs
from . import vals, funcs


class Error(Exception):
    '''builtins error'''


@dataclass(frozen=True)
class Func(funcs.AbstractFunc):
    '''builtin func'''

    func: Callable[..., vals.Val]

    @property
    def params(self) -> exprs.Params:
        spec = inspect.getfullargspec(self.func)
        if spec.varargs or spec.varkw or spec.defaults or spec.kwonlyargs or spec.kwonlydefaults:
            raise Error(f'invalid argspec {spec} for {self.func}')
        for arg in spec.args:
            if arg != 'self':
                if arg not in spec.annotations or spec.annotations[arg] != vals.Val:
                    raise Error(
                        f'invalid annotation for arg {arg} in spec {spec} for func {self.func}')
        return exprs.Params([exprs.Param(arg) for arg in spec.args])

    def apply(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        params = self.params
        if len(params) != len(args):
            raise Error(
                f'param count mismatch: expected {len(params)} got {len(args)}')
        return self.func(**{param.name: arg.value for param, arg in zip(self.params, args)})


_BUILTIN_CLASS_FUNC_PREFIX = 'func_'


@dataclass(frozen=True)
class Class(vals.AbstractClass):
    '''builtin class'''

    __object_type: Type['_Object']
    _members: vals.Scope = field(init=False, default_factory=vals.Scope)
    _name: Optional[str] = field(kw_only=True, default=None)

    def __post_init__(self):
        for name, val in self._object_type.__dict__.items():
            if name.startswith(_BUILTIN_CLASS_FUNC_PREFIX):
                func_name = name[len(_BUILTIN_CLASS_FUNC_PREFIX):]
                func = funcs.BindableFunc(Func(val))
                self._members[func_name] = func

    @property
    def name(self) -> str:
        return self._name or self._object_type.__name__

    @property
    def _object_type(self) -> Type['vals.Object']:
        return self.__object_type

    @property
    def members(self) -> vals.Scope:
        return self._members

    @staticmethod
    @cache
    def for_class(class_: Type['_Object']) -> 'Class':
        '''get the builtin class for the given builtin'''
        return Class(class_)


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

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def for_value(cls, value: _Value) -> '_ValueObject[_Value]':
        '''build an object for the given value'''
        class_ = Class.for_class(cls)
        object_: '_ValueObject[_Value]' = cls(
            class_, class_.members.as_child(), value)
        object_.bind_self()
        return object_


@dataclass(frozen=True)
class Int(_ValueObject[int]):
    '''int builtin'''

    def func___add__(self, rhs: vals.Val) -> vals.Val:
        '''add class method'''
        if not isinstance(rhs, Int):
            raise Error(f'invalid Int.__add__ rhs {rhs}')
        return Int.for_value(self.value+rhs.value)

    def func___sub__(self, rhs: vals.Val) -> vals.Val:
        '''sub class method'''
        if not isinstance(rhs, Int):
            raise Error(f'invalid Int.__sub__ rhs {rhs}')
        return Int.for_value(self.value-rhs.value)

    def func___mul__(self, rhs: vals.Val) -> vals.Val:
        '''mul class method'''
        if not isinstance(rhs, Int):
            raise Error(f'invalid Int.__mul__ rhs {rhs}')
        return Int.for_value(self.value*rhs.value)

    def func___div__(self, rhs: vals.Val) -> vals.Val:
        '''div class method'''
        if not isinstance(rhs, Int):
            raise Error(f'invalid Int.__div__ rhs {rhs}')
        return Float.for_value(self.value/rhs.value)


@dataclass(frozen=True)
class Float(_ValueObject[float]):
    '''float builtin'''

    def func___add__(self, rhs: vals.Val) -> vals.Val:
        '''add class method'''
        if not isinstance(rhs, Float):
            raise Error(f'invalid Float.__add__ rhs {rhs}')
        return Float.for_value(self.value+rhs.value)

    def func___sub__(self, rhs: vals.Val) -> vals.Val:
        '''sub class method'''
        if not isinstance(rhs, Float):
            raise Error(f'invalid Float.__sub__ rhs {rhs}')
        return Float.for_value(self.value-rhs.value)

    def func___mul__(self, rhs: vals.Val) -> vals.Val:
        '''mul class method'''
        if not isinstance(rhs, Float):
            raise Error(f'invalid Float.__mul__ rhs {rhs}')
        return Float.for_value(self.value*rhs.value)

    def func___div__(self, rhs: vals.Val) -> vals.Val:
        '''div class method'''
        if not isinstance(rhs, Float):
            raise Error(f'invalid Float.__div__ rhs {rhs}')
        return Float.for_value(self.value/rhs.value)


@ dataclass(frozen=True)
class NoneObject(_Object):
    '''None builtin'''


NoneClass = Class(NoneObject, _name='NoneClass')
none = NoneObject(NoneClass, NoneClass.members.as_child())
