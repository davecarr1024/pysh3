# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Tuple
import unittest
from . import exprs, vals, builtins_


class TestExpr(unittest.TestCase):
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
        ]):
            with self.subTest(input_str=input_str, expected_expr=expected_expr):
                self.assertEqual(expected_expr, exprs.Expr.load(input_str))


class TestRef(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Ref('a').eval(vals.Scope(
                None, {'a': builtins_.Int(value=1)})),
            exprs.Result(builtins_.Int(value=1))
        )

    def test_eval_fail(self):
        with self.assertRaises(exprs.Error):
            exprs.Ref('a').eval(vals.Scope())


class TestLiteral(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Literal(builtins_.Int(value=1)).eval(vals.Scope()),
            exprs.Result(builtins_.Int(value=1))
        )


class TestAssignment(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        exprs.Assignment('a', exprs.Literal(
            builtins_.Int(value=1))).eval(scope)
        self.assertEqual(scope['a'], builtins_.Int(value=1))


class TestNamespace(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        namespace: vals.Val = exprs.Namespace([
            exprs.Literal(builtins_.Int(value=1)),
            exprs.Assignment('a', exprs.Literal(builtins_.Int(value=2))),
        ]).eval(scope).value
        self.assertNotIn('a', scope)
        self.assertIn('a', namespace.members)
        self.assertEqual(namespace['a'], builtins_.Int(value=2))
