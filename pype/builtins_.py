'''builtins'''

from dataclasses import dataclass, field
import inspect
from typing import Callable, Optional, Type

from pype import exprs
from . import vals, funcs


class Error(Exception):
    '''builtins error'''


@dataclass(frozen=True)
class BuiltinFunc(funcs.AbstractFunc):
    '''builtin func'''

    func: Callable[[vals.Scope, vals.Args], vals.Val]

    @property
    def params(self) -> exprs.Params:
        raise NotImplementedError(inspect.getfullargspec(self.func))

    def apply(self, scope: vals.Scope, args: vals.Args) -> vals.Val:
        return self.func(scope, args)


@dataclass(frozen=True)
class BuiltinClass(vals.AbstractClass):
    '''builtin class'''

    __object_type: Type['vals.Object']
    _members: vals.Scope = field(init=False, default_factory=vals.Scope)
    _name: Optional[str] = None

    def __post_init__(self):
        # build members
        pass

    @property
    def name(self) -> str:
        return self._name or self._object_type.__name__

    @property
    def _object_type(self) -> Type['vals.Object']:
        return self.__object_type

    @property
    def members(self) -> vals.Scope:
        return self._members


@dataclass(frozen=True)
class Int(vals.Object):
    '''int builtin'''

    class_: vals.AbstractClass = field(
        default_factory=lambda: IntClass, repr=False)
    _members: vals.Scope = field(
        default_factory=lambda: IntClass.members.as_child(), repr=False)  # pylint: disable=unnecessary-lambda
    value: int = field(kw_only=True, default=0)


IntClass = BuiltinClass(Int)


@dataclass(frozen=True)
class NoneObject(vals.Object):
    '''None builtin'''

    class_: vals.AbstractClass = field(
        default_factory=lambda: NoneClass, repr=False)
    _members: vals.Scope = field(
        default_factory=lambda: NoneClass.members.as_child(), repr=False)  # pylint: disable=unnecessary-lambda


NoneClass = BuiltinClass(NoneObject, _name='NoneClass')
none = NoneObject()
