# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Tuple
import unittest
from pype import exprs, func, loader, builtins_, vals


def _int(value: int) -> builtins_.Int:
    return builtins_.Int(value=value)


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
                    [exprs.Assignment('a', exprs.Literal(_int(1)))]),
            ),
            (
                r'def f(a,b) {}',
                exprs.Namespace([
                    exprs.Assignment(
                        'f',
                        exprs.Literal(
                            func.Func(
                                'f',
                                exprs.Params(
                                    [exprs.Param('a'), exprs.Param('b')]),
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
            (
                'f(1,2);',
                exprs.Namespace([
                    exprs.Call(
                        exprs.Ref('f'),
                        exprs.Args([
                            exprs.Arg(exprs.Literal(_int(1))),
                            exprs.Arg(exprs.Literal(_int(2))),
                        ])
                    ),
                ])
            )
        ]):
            with self.subTest(input_str=input_str, expected_expr=expected_expr):
                self.assertEqual(expected_expr, loader.load(input_str))

    def test_eval(self):
        for input_str, expected_result in list[Tuple[str, vals.Val]]([
            ('1;', _int(1)),
            ('a = 1; a;', _int(1)),
            (
                r'''
                def f(a) { return a; }
                f(1);
                ''',
                _int(1)
            ),
        ]):
            with self.subTest(input_str=input_str, expected_result=expected_result):
                self.assertEqual(loader.eval_(input_str), expected_result)
