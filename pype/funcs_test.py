# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Sequence, Tuple
import unittest
from . import funcs, vals, exprs


class FuncTest(unittest.TestCase):
    def test_apply(self):
        scope = vals.Scope.default()
        self.assertEqual(
            funcs.Func(
                [
                    exprs.Assignment('a', exprs.Literal(vals.Int(value=1))),
                    exprs.Return(exprs.Ref('a')),
                    exprs.Assignment('a', exprs.Literal(vals.Int(value=2))),
                ],
                []
            ).apply(scope, []),
            vals.Int(value=1))
        self.assertNotIn('a', scope)

    def test_apply_param(self):
        scope = vals.Scope.default()
        self.assertEqual(
            funcs.Func(
                [
                    exprs.Return(exprs.Ref('a')),
                ],
                ['a']
            ).apply(scope, [vals.Int(value=1)]),
            vals.Int(value=1))
        self.assertNotIn('a', scope)

    def test_apply_fail(self):
        for func, args in list[Tuple[funcs.Func, Sequence[vals.Val]]]([
            (
                funcs.Func([], ['a']),
                [],
            ),
            (
                funcs.Func([], ['a']),
                [vals.Int(value=1), vals.Int(value=2)],
            ),
        ]):
            with self.subTest(func=func, args=args):
                with self.assertRaises(funcs.Error):
                    func.apply(vals.Scope.default(), args)


class BuiltinFuncTest(unittest.TestCase):
    def test_apply(self):
        self.assertEqual(
            funcs.BuiltinFunc(lambda scope, args: vals.Int(
                value=1)).apply(vals.Scope.default(), []),
            vals.Int(value=1)
        )
