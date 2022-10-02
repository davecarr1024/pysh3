# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from pype import errors, exprs, vals, builtins_

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    # pylint: disable=protected-access
    __import__(
        'sys').modules['unittest.util']._MAX_LENGTH = 999999999
    # pylint: enable=protected-access


def _int(value: int) -> vals.Val:
    return builtins_.Int.for_value(value)


def _int_literal(value: int) -> exprs.Literal:
    return exprs.Literal(_int(value))


class TestArg(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Arg(_int_literal(1)
                      ).eval(vals.Scope()),
            vals.Arg(_int(1))
        )


class TestArgs(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Args([
                exprs.Arg(_int_literal(1)),
                exprs.Arg(_int_literal(2)),
            ]).eval(vals.Scope()),
            vals.Args([
                vals.Arg(_int(1)),
                vals.Arg(_int(2)),
            ])
        )


class TestRef(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Ref('a').eval(vals.Scope({'a': _int(1)})),
            _int(1)
        )

    def test_eval_fail(self):
        with self.assertRaises(errors.Error):
            exprs.Ref('a').eval(vals.Scope())


class TestLiteral(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            _int_literal(1).eval(vals.Scope()),
            _int(1)
        )


class TestBinaryOperation(unittest.TestCase):
    def test_add(self):
        self.assertEqual(
            exprs.BinaryOperation(
                exprs.BinaryOperation.Operator.ADD,
                _int_literal(1),
                _int_literal(2),
            ).eval(vals.Scope()),
            _int(3)
        )

    def test_sub(self):
        self.assertEqual(
            exprs.BinaryOperation(
                exprs.BinaryOperation.Operator.SUB,
                _int_literal(1),
                _int_literal(2),
            ).eval(vals.Scope()),
            _int(-1)
        )

    def test_mul(self):
        self.assertEqual(
            exprs.BinaryOperation(
                exprs.BinaryOperation.Operator.MUL,
                _int_literal(1),
                _int_literal(2),
            ).eval(vals.Scope()),
            _int(2)
        )

    def test_div(self):
        self.assertEqual(
            exprs.BinaryOperation(
                exprs.BinaryOperation.Operator.DIV,
                _int_literal(1),
                _int_literal(2),
            ).eval(vals.Scope()),
            builtins_.Float.for_value(0.5)
        )
