# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,duplicate-code

from typing import Tuple
import unittest
from pype import builtins_, exprs, func, loader, params, statements

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
                            builtins_.Int.for_value(1)
                        )
                    )
                ])
            ),
            (
                '1.a;',
                statements.Block([
                    statements.ExprStatement(
                        exprs.Path(
                            exprs.Literal(builtins_.Int.for_value(1)),
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
                        exprs.Literal(builtins_.Int.for_value(1))
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
                                exprs.Literal(builtins_.Int.for_value(1))
                            )
                        ])
                    ),
                ])
            ),
            #             (
            #                 'a = b;',
            #                 exprs.Namespace([exprs.Assignment('a', exprs.Ref('b'))]),
            #             ),
            #             (
            #                 'a = 1;',
            #                 exprs.Namespace(
            #                     [exprs.Assignment('a', exprs.Literal(builtins_.Int.for_value(1)))]),
            #             ),
            #             (
            #                 r'def f(a,b) {}',
            #                 exprs.Namespace([
            #                     exprs.Assignment(
            #                         'f',
            #                         exprs.Literal(
            #                             func.Func(
            #                                 'f',
            #                                 params.Params(
            #                                     [params.Param('a'), params.Param('b')]),
            #                                 [],
            #                             )
            #                         )
            #                     ),
            #                 ]),
            #             ),
            #             (
            #                 'return;',
            #                 exprs.Namespace([func.Return(None)]),
            #             ),
            #             (
            #                 'return a;',
            #                 exprs.Namespace([func.Return(exprs.Ref('a'))]),
            #             ),
            #             (
            #                 'f(1,2);',
            #                 exprs.Namespace([
            #                     exprs.Path(
            #                         exprs.Ref('f'),
            #                         [
            #                             exprs.Path.Call(exprs.Args([
            #                                 exprs.Arg(exprs.Literal(
            #                                     builtins_.Int.for_value(1))),
            #                                 exprs.Arg(exprs.Literal(
            #                                     builtins_.Int.for_value(2))),
            #                             ]))
            #                         ]
            #                     )
            #                 ])
            #             ),
            #             (
            #                 '1 + 2;',
            #                 exprs.Namespace([
            #                     exprs.Path(
            #                         exprs.Literal(builtins_.Int.for_value(1)),
            #                         [
            #                             exprs.Path.Member('__add__'),
            #                             exprs.Path.Call(exprs.Args([
            #                                 exprs.Arg(exprs.Literal(
            #                                     builtins_.Int.for_value(2))),
            #                             ]))
            #                         ]
            #                     )
            #                 ])
            #             ),
            #             (
            #                 '1 - 2;',
            #                 exprs.Namespace([
            #                     exprs.Path(
            #                         exprs.Literal(builtins_.Int.for_value(1)),
            #                         [
            #                             exprs.Path.Member('__sub__'),
            #                             exprs.Path.Call(exprs.Args([
            #                                 exprs.Arg(exprs.Literal(
            #                                     builtins_.Int.for_value(2))),
            #                             ]))
            #                         ]
            #                     )
            #                 ])
            #             ),
            #             (
            #                 '1 * 2;',
            #                 exprs.Namespace([
            #                     exprs.Path(
            #                         exprs.Literal(builtins_.Int.for_value(1)),
            #                         [
            #                             exprs.Path.Member('__mul__'),
            #                             exprs.Path.Call(exprs.Args([
            #                                 exprs.Arg(exprs.Literal(
            #                                     builtins_.Int.for_value(2))),
            #                             ]))
            #                         ]
            #                     )
            #                 ])
            #             ),
            #             (
            #                 '1 / 2;',
            #                 exprs.Namespace([
            #                     exprs.Path(
            #                         exprs.Literal(builtins_.Int.for_value(1)),
            #                         [
            #                             exprs.Path.Member('__div__'),
            #                             exprs.Path.Call(exprs.Args([
            #                                 exprs.Arg(exprs.Literal(
            #                                     builtins_.Int.for_value(2))),
            #                             ]))
            #                         ]
            #                     )
            #                 ])
            #             ),
            #             (
            #                 'class c { a; }',
            #                 exprs.Namespace([
            #                     exprs.Assignment(
            #                         'c',
            #                         exprs.Class(
            #                             'c',
            #                             [
            #                                 exprs.Ref('a'),
            #                             ]
            #                         )
            #                     ),
            #                 ])
            #             ),
        ]):
            with self.subTest(input_str=input_str, expected_block=expected_block):
                actual_block = loader.load(input_str)
                self.assertEqual(actual_block, expected_block,
                                 f'actual {actual_block} != expected {expected_block}')

#     def test_eval(self):
#         for input_str, expected_result in list[Tuple[str, vals.Val]]([
#             ('1;', builtins_.Int.for_value(1)),
#             ('a = 1; a;', builtins_.Int.for_value(1)),
#             (
#                 r'''
#                 def f(a) { return a; }
#                 f(1);
#                 ''',
#                 builtins_.Int.for_value(1)
#             ),
#             ('1 + 2;', builtins_.Int.for_value(3)),
#             ('1 - 2;', builtins_.Int.for_value(-1)),
#             ('1 * 2;', builtins_.Int.for_value(2)),
#             ('1 / 2;', builtins_.Float.for_value(0.5)),
#             (
#                 'def f(a,b) { return a + b; } f(1,2);',
#                 builtins_.Int.for_value(3)
#             ),
#             (
#                 'class c { a = 1; } c.a;',
#                 builtins_.Int.for_value(1)
#             ),
#             (
#                 'class c { a = 1; } c().a;',
#                 builtins_.Int.for_value(1)
#             ),
#         ]):
#             with self.subTest(input_str=input_str, expected_result=expected_result):
#                 self.assertEqual(loader.eval_(input_str), expected_result)
