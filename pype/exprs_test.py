# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from . import exprs, vals, builtins_


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
