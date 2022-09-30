# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Tuple
import unittest

from pype import funcs


class TestParams(unittest.TestCase):
    def test_len(self):
        for params, expected_len in list[Tuple[funcs.Params, int]]([
            (funcs.Params([]), 0),
            (funcs.Params([funcs.Param('a'), funcs.Param('b')]), 2),
        ]):
            with self.subTest(params=params, expected_len=expected_len):
                self.assertEqual(len(params), expected_len)

    def test_tail(self):
        self.assertEqual(
            funcs.Params([funcs.Param('a'), funcs.Param('b')]).tail,
            funcs.Params([funcs.Param('b')])
        )

    def test_tail_fail(self):
        with self.assertRaises(funcs.Error):
            _ = funcs.Params([]).tail

# TODO(TestBindableFunc/TestBoundFunc)
