# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from pype import exprs, statements, vals, builtins_

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    # pylint: disable=protected-access
    __import__(
        'sys').modules['unittest.util']._MAX_LENGTH = 999999999
    # pylint: enable=protected-access


class BlockTest(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        self.assertEqual(
            statements.Block([
                statements.Assignment('a', exprs.Literal(
                    builtins_.Int.for_value(1))),
            ]).eval(scope),
            statements.Result()
        )
        self.assertEqual(scope['a'], builtins_.Int.for_value(1))

    def test_eval_return(self):
        scope = vals.Scope()
        self.assertEqual(
            statements.Block([
                statements.Return(None),
                statements.Assignment('a', exprs.Literal(
                    builtins_.Int.for_value(1))),
            ]).eval(scope),
            statements.Result(return_=statements.Result.Return(None))
        )
        self.assertNotIn('a', scope)

    def test_eval_return_val(self):
        scope = vals.Scope()
        self.assertEqual(
            statements.Block([
                statements.Return(exprs.Literal(builtins_.Int.for_value(1))),
                statements.Assignment('a', exprs.Literal(
                    builtins_.Int.for_value(2))),
            ]).eval(scope),
            statements.Result(return_=statements.Result.Return(
                builtins_.Int.for_value(1)))
        )
        self.assertNotIn('a', scope)


class AssignmentTest(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        self.assertEqual(
            statements.Assignment('a', exprs.Literal(
                builtins_.Int.for_value(1))).eval(scope),
            statements.Result()
        )
        self.assertEqual(scope['a'], builtins_.Int.for_value(1))


class ExprStatementTest(unittest.TestCase):
    def test_eval(self):
        self.assertEqual(
            statements.ExprStatement(
                exprs.Literal(builtins_.Int.for_value(1))).eval(vals.Scope()),
            statements.Result()
        )


class ReturnTest(unittest.TestCase):
    def test_eval_empty(self):
        self.assertEqual(
            statements.Return(None).eval(vals.Scope()),
            statements.Result(return_=statements.Result.Return(None))
        )

    def test_eval_val(self):
        self.assertEqual(
            statements.Return(exprs.Literal(
                builtins_.Int.for_value(1))).eval(vals.Scope()),
            statements.Result(return_=statements.Result.Return(
                builtins_.Int.for_value(1)))
        )


class ClassTest(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        self.assertEqual(
            statements.Class(
                'c',
                statements.Block([
                    statements.Assignment('a', exprs.Literal(
                        builtins_.Int.for_value(1))),
                ])
            ).eval(scope),
            statements.Result()
        )
        self.assertEqual(
            scope['c'],
            vals.Class(
                'c',
                vals.Scope({
                    'a': builtins_.Int.for_value(1),
                })
            )
        )


class NamespaceTest(unittest.TestCase):
    def test_eval(self):
        scope = vals.Scope()
        self.assertEqual(
            statements.Namespace(
                statements.Block([
                    statements.Assignment('a', exprs.Literal(
                        builtins_.Int.for_value(1))),
                ]),
                _name='n',
            ).eval(scope),
            statements.Result()
        )
        self.assertEqual(
            scope['n'],
            vals.Namespace(
                vals.Scope({
                    'a': builtins_.Int.for_value(1),
                }),
                name='n',
            )
        )
