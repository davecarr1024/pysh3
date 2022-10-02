# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from pype import errors, exprs, vals, builtins_

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    # pylint: disable=protected-access
    __import__(
        'sys').modules['unittest.util']._MAX_LENGTH = 999999999
    # pylint: enable=protected-access


class TestArg(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Arg(exprs.Literal(builtins_.Int.for_value(1))
                      ).eval(vals.Scope()),
            vals.Arg(builtins_.Int.for_value(1))
        )


class TestArgs(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Args([
                exprs.Arg(exprs.Literal(builtins_.Int.for_value(1))),
                exprs.Arg(exprs.Literal(builtins_.Int.for_value(2))),
            ]).eval(vals.Scope()),
            vals.Args([
                vals.Arg(builtins_.Int.for_value(1)),
                vals.Arg(builtins_.Int.for_value(2)),
            ])
        )


class TestRef(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Ref('a').eval(vals.Scope({'a': builtins_.Int.for_value(1)})),
            builtins_.Int.for_value(1)
        )

    def test_eval_fail(self):
        with self.assertRaises(errors.Error):
            exprs.Ref('a').eval(vals.Scope())


class TestLiteral(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Literal(builtins_.Int.for_value(1)).eval(vals.Scope()),
            builtins_.Int.for_value(1)
        )
