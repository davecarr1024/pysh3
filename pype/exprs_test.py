# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from . import exprs, vals


class TestRef(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Ref('a').eval(vals.Scope(
                None, {'a': vals.Int(value=1)})),
            exprs.Result(vals.Int(value=1))
        )

    def test_eval_fail(self):
        with self.assertRaises(exprs.Error):
            exprs.Ref('a').eval(vals.Scope())


class TestLiteral(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Literal(vals.Int(value=1)).eval(vals.Scope()),
            exprs.Result(vals.Int(value=1))
        )


class TestAssignment(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        exprs.Assignment('a', exprs.Literal(vals.Int(value=1))).eval(scope)
        self.assertEqual(scope['a'], vals.Int(value=1))


class TestReturn(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Return(exprs.Literal(vals.Int(value=1))
                         ).eval(vals.Scope()),
            exprs.Result(vals.Int(value=1), is_return=True)
        )
