# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Tuple
import unittest
from pype import errors, exprs, func, statements, vals, builtins_, params


class FuncTest(unittest.TestCase):
    def test_apply(self):
        for func_, args, expected_result in list[Tuple[func.Func, vals.Args, vals.Val]]([
            (
                func.Func('f', params.Params([]), statements.Block([])),
                vals.Args([]),
                builtins_.none,
            ),
            (
                func.Func(
                    'f',
                    params.Params([]),
                    statements.Block([
                        statements.Assignment(
                            'a',
                            exprs.Literal(builtins_.Int.for_value(1)),
                        ),
                    ]),
                ),
                vals.Args([]),
                builtins_.none,
            ),
            (
                func.Func(
                    'f',
                    params.Params([]),
                    statements.Block([
                        statements.Return(
                            exprs.Literal(builtins_.Int.for_value(1))
                        ),
                    ]),
                ),
                vals.Args([]),
                builtins_.Int.for_value(1),
            ),
            (
                func.Func(
                    'f',
                    params.Params([
                        params.Param('a'),
                    ]),
                    statements.Block([
                        statements.Return(
                            exprs.Ref('a'),
                        ),
                    ]),
                ),
                vals.Args([
                    vals.Arg(builtins_.Int.for_value(1)),
                ]),
                builtins_.Int.for_value(1),
            ),
        ]):
            with self.subTest(func_=func_, args=args, expected_result=expected_result):
                actual_result = func_.apply(vals.Scope(), args)
                self.assertEqual(expected_result, actual_result)

    def test_apply_fail(self):
        for func_, args in list[Tuple[func.Func, vals.Args]]([
            (
                func.Func(
                    'f',
                    params.Params([]),
                    statements.Block([]),
                ),
                vals.Args([
                    vals.Arg(builtins_.Int.for_value(1)),
                ])
            ),
            (
                func.Func(
                    'f',
                    params.Params([
                        params.Param('a'),
                    ]),
                    statements.Block([]),
                ),
                vals.Args([])
            ),
        ]):
            with self.subTest(func_=func_, args=args):
                with self.assertRaises(errors.Error):
                    func_.apply(vals.Scope(), args)
