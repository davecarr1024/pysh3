# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

from typing import Tuple
import unittest
from pype import exprs, func, vals, builtins_

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


class TestParam(unittest.TestCase):
    def test_bind(self):
        scope = vals.Scope()
        exprs.Param('a').bind(scope, vals.Arg(builtins_.Int.for_value(1)))
        self.assertEqual(
            scope['a'],
            builtins_.Int.for_value(1)
        )


class TestParams(unittest.TestCase):
    def test_len(self):
        for params, expected_len in list[Tuple[exprs.Params, int]]([
            (exprs.Params([]), 0),
            (exprs.Params([exprs.Param('a'), exprs.Param('b')]), 2),
        ]):
            with self.subTest(params=params, expected_len=expected_len):
                self.assertEqual(len(params), expected_len)

    def test_tail(self):
        self.assertEqual(
            exprs.Params([exprs.Param('a'), exprs.Param('b')]).tail,
            exprs.Params([exprs.Param('b')])
        )

    def test_tail_fail(self):
        with self.assertRaises(exprs.Error):
            _ = exprs.Params([]).tail

    def test_bind(self):
        self.assertEqual(
            exprs.Params([
                exprs.Param('a'),
                exprs.Param('b'),
            ]).bind(vals.Scope(), vals.Args([
                vals.Arg(builtins_.Int.for_value(1)),
                vals.Arg(builtins_.Int.for_value(2)),
            ])),
            vals.Scope(vals.Scope(), {
                'a': builtins_.Int.for_value(1),
                'b': builtins_.Int.for_value(2),
            })
        )

    def test_bind_fail(self):
        with self.assertRaises(exprs.Error):
            exprs.Params([exprs.Param('a')]).bind(vals.Scope(), vals.Args([]))


class TestRef(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Ref('a').eval(vals.Scope(
                None, {'a': builtins_.Int.for_value(1)})),
            exprs.Result(builtins_.Int.for_value(1))
        )

    def test_eval_fail(self):
        with self.assertRaises(exprs.Error):
            exprs.Ref('a').eval(vals.Scope())


class TestLiteral(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Literal(builtins_.Int.for_value(1)).eval(vals.Scope()),
            exprs.Result(builtins_.Int.for_value(1))
        )


class TestAssignment(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        exprs.Assignment('a', exprs.Literal(
            builtins_.Int.for_value(1))).eval(scope)
        self.assertEqual(scope['a'], builtins_.Int.for_value(1))


class TestNamespace(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        namespace: vals.Val = exprs.Namespace([
            exprs.Literal(builtins_.Int.for_value(1)),
            exprs.Assignment('a', exprs.Literal(builtins_.Int.for_value(2))),
        ]).eval(scope).value
        self.assertNotIn('a', scope)
        self.assertIn('a', namespace.members)
        self.assertEqual(namespace['a'], builtins_.Int.for_value(2))


class TestCall(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            exprs.Namespace([
                exprs.Assignment(
                    'f',
                    exprs.Literal(func.Func(
                        'f',
                        exprs.Params([exprs.Param('a'), exprs.Param('b')]),
                        [
                            func.Return(exprs.Ref('a')),
                        ],
                    ))
                ),
                exprs.Assignment(
                    'c',
                    exprs.Path(
                        exprs.Ref('f'),
                        [
                            exprs.Path.Call(exprs.Args([
                                exprs.Arg(exprs.Literal(
                                    builtins_.Int.for_value(1))),
                                exprs.Arg(exprs.Literal(
                                    builtins_.Int.for_value(2))),
                            ])),
                        ]
                    )
                )
            ]).eval(vals.Scope()).value.members['c'],
            builtins_.Int.for_value(1))


class TestClass(unittest.TestCase):
    def test_eval(self):
        c = exprs.Class(
            'c',
            [
                exprs.Assignment('a', exprs.Literal(
                    builtins_.Int.for_value(1))),
            ]
        ).eval(vals.Scope()).value
        self.assertEqual(
            c,
            vals.Class(
                'c',
                vals.Scope(
                    vals.Scope(),
                    {
                        'a': builtins_.Int.for_value(1),
                    }
                )
            )
        )
        self.assertIn('a', c)
        self.assertEqual(c['a'], builtins_.Int.for_value(1))
