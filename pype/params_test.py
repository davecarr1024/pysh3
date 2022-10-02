# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Tuple
import unittest
from pype import builtins_, errors, params, vals


class ParamsTest(unittest.TestCase):
    def test_tail(self):
        self.assertEqual(
            params.Params([
                params.Param('a'),
                params.Param('b'),
            ]).tail,
            params.Params([
                params.Param('b'),
            ])
        )

    def test_tail_fail(self):
        with self.assertRaises(errors.Error):
            _ = params.Params([]).tail

    def test_len(self):
        for params_, expected_len in list[Tuple[params.Params, int]]([
            (params.Params([]), 0),
            (params.Params([params.Param('a'), params.Param('b')]), 2),
        ]):
            with self.subTest(params=params_, expected_len=expected_len):
                self.assertEqual(len(params_), expected_len)

    def test_bind(self):
        self.assertEqual(
            params.Params([
                params.Param('a'),
                params.Param('b'),
            ]).bind(vals.Scope(), vals.Args([
                vals.Arg(builtins_.Int.for_value(1)),
                vals.Arg(builtins_.Int.for_value(2)),
            ])),
            vals.Scope({
                'a': builtins_.Int.for_value(1),
                'b': builtins_.Int.for_value(2),
            })
        )

    def test_bind_fail(self):
        with self.assertRaises(errors.Error):
            params.Params([params.Param('a')]).bind(
                vals.Scope(), vals.Args([]))
