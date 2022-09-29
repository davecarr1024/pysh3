# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Sequence, Tuple
import unittest
from . import func, funcs, vals, exprs, builtins_


class TestReturn(unittest.TestCase):
    def test_eval(self):
        for return_, expected_result in list[Tuple[func.Return, exprs.Result]]([
            (
                func.Return(exprs.Literal(builtins_.Int(value=1))),
                exprs.Result(builtins_.Int(value=1), is_return=True)
            ),
            (
                func.Return(None),
                exprs.Result(builtins_.none, is_return=True)
            ),
        ]):
            with self.subTest(return_=return_, expected_result=expected_result):
                self.assertEqual(
                    return_.eval(vals.Scope()),
                    expected_result
                )


class TestFunc(unittest.TestCase):
    def test_apply(self):
        scope = vals.Scope.default()
        self.assertEqual(
            func.Func(
                [
                    exprs.Assignment('a', exprs.Literal(
                        builtins_.Int(value=1))),
                    func.Return(exprs.Ref('a')),
                    exprs.Assignment('a', exprs.Literal(
                        builtins_.Int(value=2))),
                ],
                []
            ).apply(scope, []),
            builtins_.Int(value=1))
        self.assertNotIn('a', scope)

    def test_apply_param(self):
        scope = vals.Scope.default()
        self.assertEqual(
            func.Func(
                [
                    func.Return(exprs.Ref('a')),
                ],
                ['a']
            ).apply(scope, [builtins_.Int(value=1)]),
            builtins_.Int(value=1))
        self.assertNotIn('a', scope)

    def test_apply_fail(self):
        for func_, args in list[Tuple[func.Func, Sequence[vals.Val]]]([
            (
                func.Func([], ['a']),
                [],
            ),
            (
                func.Func([], ['a']),
                [builtins_.Int(value=1), builtins_.Int(value=2)],
            ),
        ]):
            with self.subTest(func=func_, args=args):
                with self.assertRaises(funcs.Error):
                    func_.apply(vals.Scope.default(), args)