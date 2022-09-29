# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from . import builtins_


class NoneTest(unittest.TestCase):
    def test_class(self):
        self.assertEqual('NoneClass', builtins_.NoneClass.name)

    def test_eq(self):
        self.assertEqual(builtins_.none, builtins_.none)


class IntTest(unittest.TestCase):
    def test_int_class(self):
        self.assertEqual('Int', builtins_.IntClass.name)

    def test_eq(self):
        self.assertEqual(builtins_.Int(value=1), builtins_.Int(value=1))
        self.assertNotEqual(builtins_.Int(value=1), builtins_.Int(value=2))
