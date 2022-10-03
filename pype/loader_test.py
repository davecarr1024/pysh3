# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,duplicate-code

from typing import Tuple
import unittest
from pype import builtins_, exprs, func, loader, params, statements, vals

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    # pylint: disable=protected-access
    __import__(
        'sys').modules['unittest.util']._MAX_LENGTH = 999999999
    # pylint: enable=protected-access


class TestLoader(unittest.TestCase):
    def test_load(self):
        for input_str, expected_block in list[Tuple[str, statements.Block]]([
            (
                'a;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.Ref('a')
                    )
                ])
            ),
            (
                'a.b;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.Path(
                            exprs.Ref('a'),
                            [
                                exprs.Path.Member('b'),
                            ]
                        ),
                    )
                ])
            ),
            (
                'a(b);',
                statements.Block([
                    statements.ExprStatement(
                        exprs.Path(
                            exprs.Ref('a'),
                            [
                                exprs.Path.Call(
                                    exprs.Args([
                                        exprs.Arg(exprs.Ref('b')),
                                    ])
                                ),
                            ]
                        ),
                    )
                ])
            ),
            (
                '1;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.Literal(
                            builtins_.int_(1)
                        )
                    )
                ])
            ),
            (
                '1.a;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.Path(
                            exprs.Literal(builtins_.int_(1)),
                            [
                                exprs.Path.Member('a'),
                            ]
                        ),
                    )
                ])
            ),
            (
                'a = 1;',
                statements.Block([
                    statements.Assignment(
                        'a',
                        exprs.Literal(builtins_.int_(1))
                    )
                ])
            ),
            (
                'return;',
                statements.Block([
                    statements.Return(None),
                ])
            ),
            (
                'return a;',
                statements.Block([
                    statements.Return(
                        exprs.Ref('a')
                    ),
                ])
            ),
            (
                'def f(a,b) { return a; }',
                statements.Block([
                    func.Decl(
                        'f',
                        params.Params([
                            params.Param('a'),
                            params.Param('b'),
                        ]),
                        statements.Block([
                            statements.Return(exprs.Ref('a')),
                        ])
                    )
                ])
            ),
            (
                'class c { a = 1; }',
                statements.Block([
                    statements.Class(
                        'c',
                        statements.Block([
                            statements.Assignment(
                                'a',
                                exprs.Literal(builtins_.int_(1))
                            )
                        ])
                    ),
                ])
            ),
            (
                'a + b;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.BinaryOperation(
                            exprs.BinaryOperation.Operator.ADD,
                            exprs.Ref('a'),
                            exprs.Ref('b'),
                        )
                    ),
                ])
            ),
            (
                'a - b;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.BinaryOperation(
                            exprs.BinaryOperation.Operator.SUB,
                            exprs.Ref('a'),
                            exprs.Ref('b'),
                        )
                    ),
                ])
            ),
            (
                'a * b;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.BinaryOperation(
                            exprs.BinaryOperation.Operator.MUL,
                            exprs.Ref('a'),
                            exprs.Ref('b'),
                        )
                    ),
                ])
            ),
            (
                'a / b;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.BinaryOperation(
                            exprs.BinaryOperation.Operator.DIV,
                            exprs.Ref('a'),
                            exprs.Ref('b'),
                        )
                    ),
                ])
            ),
            (
                '3.14;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.Literal(builtins_.float_(3.14))
                    ),
                ])
            ),
            (
                r"'a';",
                statements.Block([
                    statements.ExprStatement(
                        exprs.Literal(builtins_.str_('a'))
                    ),
                ])
            ),
        ]):
            with self.subTest(input_str=input_str, expected_block=expected_block):
                actual_block = loader.load(input_str)
                self.assertEqual(actual_block, expected_block,
                                 f'actual {actual_block} != expected {expected_block}')

    def test_eval(self):
        for input_str, expected_result in list[Tuple[str, vals.Val]]([
            ('1;', builtins_.int_(1)),
            ('a = 1; a;', builtins_.int_(1)),
            (
                r'''
                def f(a) { return a; }
                f(1);
                ''',
                builtins_.int_(1)
            ),
            ('1 + 2;', builtins_.int_(3)),
            ('1 - 2;', builtins_.int_(-1)),
            ('1 * 2;', builtins_.int_(2)),
            ('10 / 5;', builtins_.int_(2)),
            (
                'def f(a,b) { return a + b; } f(1,2);',
                builtins_.int_(3)
            ),
            (
                'class c { a = 1; } c.a;',
                builtins_.int_(1)
            ),
            (
                'class c { a = 1; } c().a;',
                builtins_.int_(1)
            ),
        ]):
            with self.subTest(input_str=input_str, expected_result=expected_result):
                self.assertEqual(loader.eval_(input_str), expected_result)
