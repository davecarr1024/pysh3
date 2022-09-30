# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Callable, Tuple
import unittest
from pype import builtins_, exprs, funcs, vals

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    # pylint: disable=protected-access
    __import__(
        'sys').modules['unittest.util']._MAX_LENGTH = 999999999
    # pylint: enable=protected-access


class BuiltinFuncTest(unittest.TestCase):
    def test_params(self):
        def f_1(unused_a: vals.Val, unused_b: vals.Val) -> vals.Val:
            ...

        def f_2() -> vals.Val:
            ...

        for func, expected_params in list[Tuple[Callable[..., vals.Val], exprs.Params]]([
            (
                f_1,
                exprs.Params([exprs.Param('unused_a'),
                             exprs.Param('unused_b')])
            ),
            (f_2, exprs.Params([])),
        ]):
            with self.subTest(func=func, expected_params=expected_params):
                self.assertEqual(
                    builtins_.Func(func).params,
                    expected_params
                )

    def test_params_fail(self):
        def kwargs(**unused_kwargs: vals.Val) -> vals.Val:
            ...

        def args(*unused_args: vals.Val) -> vals.Val:
            ...

        def default_arg(unused_a: vals.Val = builtins_.Int.for_value(1)) -> vals.Val:
            ...

        for func in list[Callable[..., vals.Val]]([
            kwargs,
            args,
            default_arg,
        ]):
            with self.subTest(func=func):
                with self.assertRaises(builtins_.Error):
                    _ = builtins_.Func(func).params

    def test_apply(self):
        def f_1() -> vals.Val:
            return builtins_.Int.for_value(1)

        def f_2(val: vals.Val) -> vals.Val:
            assert isinstance(val, builtins_.Int), val
            return builtins_.Int.for_value(val.value*2)

        for func, args, expected_result in (
                list[Tuple[Callable[..., vals.Val], vals.Args, vals.Val]]([
                    (
                        f_1,
                        vals.Args([]),
                        builtins_.Int.for_value(1),
                    ),
                    (
                        f_2,
                        vals.Args([vals.Arg(builtins_.Int.for_value(2))]),
                        builtins_.Int.for_value(4),
                    ),
                ])):
            with self.subTest(func=func, args=args, expected_result=expected_result):
                self.assertEqual(
                    builtins_.Func(func).apply(
                        vals.Scope.default(), args),
                    expected_result
                )


class NoneTest(unittest.TestCase):
    def test_class(self):
        self.assertEqual('NoneClass', builtins_.NoneClass.name)

    def test_eq(self):
        self.assertEqual(builtins_.none, builtins_.none)


class IntTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(builtins_.Int.for_value(1),
                         builtins_.Int.for_value(1))
        self.assertNotEqual(builtins_.Int.for_value(1),
                            builtins_.Int.for_value(2))

    def test_add(self):
        val = builtins_.Int.for_value(1)
        self.assertIn('__add__', val)
        add_func = val['__add__']
        assert isinstance(add_func, funcs.AbstractFunc)
        self.assertEqual(
            add_func.params,
            exprs.Params([exprs.Param('rhs')])
        )
        self.assertEqual(
            builtins_.Int.for_value(1)['__add__'].apply(
                vals.Scope.default(), vals.Args([vals.Arg(builtins_.Int.for_value(2))])),
            builtins_.Int.for_value(3)
        )
