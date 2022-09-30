# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Tuple
import unittest
from pype import exprs, func, funcs, loader, builtins_


class TestLoader(unittest.TestCase):
    def test_load(self):
        for input_str, expected_expr in list[Tuple[str, exprs.Expr]]([
            (
                'a;',
                exprs.Namespace([exprs.Ref('a')]),
            ),
            (
                'a = b;',
                exprs.Namespace([exprs.Assignment('a', exprs.Ref('b'))]),
            ),
            (
                'a = 1;',
                exprs.Namespace(
                    [exprs.Assignment('a', exprs.Literal(builtins_.Int(value=1)))]),
            ),
            (
                r'def f(a,b) {}',
                exprs.Namespace([
                    exprs.Assignment(
                        'f',
                        exprs.Literal(
                            func.Func(
                                'f',
                                funcs.Params(
                                    [funcs.Param('a'), funcs.Param('b')]),
                                [],
                            )
                        )
                    ),
                ]),
            ),
            (
                'return;',
                exprs.Namespace([func.Return(None)]),
            ),
            (
                'return a;',
                exprs.Namespace([func.Return(exprs.Ref('a'))]),
            ),
        ]):
            with self.subTest(input_str=input_str, expected_expr=expected_expr):
                self.assertEqual(expected_expr, loader.load(input_str))
