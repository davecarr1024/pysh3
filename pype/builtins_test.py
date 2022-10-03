# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from pype import builtins_, vals


class BoolTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(builtins_.bool_(True), builtins_.bool_(True))
        self.assertNotEqual(builtins_.bool_(True), builtins_.bool_(False))

    def test_and(self):
        self.assertEqual(
            builtins_.bool_(True)['__and__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.bool_(False))])),
            builtins_.bool_(False)
        )

    def test_or(self):
        self.assertEqual(
            builtins_.bool_(True)['__or__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.bool_(False))])),
            builtins_.bool_(True)
        )


class IntTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(builtins_.int_(1), builtins_.int_(1))
        self.assertNotEqual(builtins_.int_(1), builtins_.int_(2))

    def test_add(self):
        self.assertEqual(
            builtins_.int_(1)['__add__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.int_(2))])),
            builtins_.int_(3)
        )

    def test_sub(self):
        self.assertEqual(
            builtins_.int_(1)['__sub__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.int_(2))])),
            builtins_.int_(-1)
        )

    def test_mul(self):
        self.assertEqual(
            builtins_.int_(1)['__mul__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.int_(2))])),
            builtins_.int_(2)
        )

    def test_div(self):
        self.assertEqual(
            builtins_.int_(10)['__div__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.int_(5))])),
            builtins_.int_(2)
        )


class FloatTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(builtins_.float_(1), builtins_.float_(1))
        self.assertNotEqual(builtins_.float_(1), builtins_.float_(2))

    def test_add(self):
        self.assertEqual(
            builtins_.float_(1)['__add__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.float_(2))])),
            builtins_.float_(3)
        )

    def test_sub(self):
        self.assertEqual(
            builtins_.float_(1)['__sub__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.float_(2))])),
            builtins_.float_(-1)
        )

    def test_mul(self):
        self.assertEqual(
            builtins_.float_(1)['__mul__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.float_(2))])),
            builtins_.float_(2)
        )

    def test_div(self):
        self.assertEqual(
            builtins_.float_(1)['__div__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.float_(2))])),
            builtins_.float_(0.5)
        )


class StrTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(builtins_.str_('a'), builtins_.str_('a'))
        self.assertNotEqual(builtins_.str_('a'), builtins_.str_('b'))

    def test_add(self):
        self.assertEqual(
            builtins_.str_('a')['__add__'].apply(
                vals.Scope(), vals.Args([vals.Arg(builtins_.str_('b'))])),
            builtins_.str_('ab')
        )


class NoneTest(unittest.TestCase):
    def test_eq_(self):
        self.assertEqual(builtins_.none, builtins_.none)
