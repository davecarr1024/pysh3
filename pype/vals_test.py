# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from pype import builtins_, vals


class ArgsTest(unittest.TestCase):
    def test_prepend(self):
        self.assertEqual(
            vals.Args([
                vals.Arg(builtins_.Int.for_value(2)),
            ]).prepend(vals.Arg(builtins_.Int.for_value(1))),
            vals.Args([
                vals.Arg(builtins_.Int.for_value(1)),
                vals.Arg(builtins_.Int.for_value(2)),
            ]))


class ScopeTest(unittest.TestCase):
    def test_contains(self):
        self.assertIn('a', vals.Scope({'a': vals.Val()}))
        self.assertNotIn('a', vals.Scope({}))

    def test_get_item(self):
        self.assertEqual(
            vals.Scope({'a': builtins_.Int.for_value(1)})['a'],
            builtins_.Int.for_value(1)
        )

    def test_set_item(self):
        scope = vals.Scope({})
        self.assertNotIn('a', scope)
        scope['a'] = builtins_.Int.for_value(1)
        self.assertIn('a', scope)
        self.assertEqual(scope['a'], builtins_.Int.for_value(1))

    def test_vals(self):
        self.assertDictEqual(
            vals.Scope(
                {
                    'b': builtins_.Int.for_value(2),
                },
                parent=vals.Scope(
                    {
                        'a': builtins_.Int.for_value(1),
                    }
                )
            ).vals,
            {
                'b': builtins_.Int.for_value(2),
            }
        )

    def test_all_vals(self):
        self.assertDictEqual(
            vals.Scope(
                {
                    'b': builtins_.Int.for_value(2),
                },
                parent=vals.Scope(
                    {
                        'a': builtins_.Int.for_value(1),
                    }
                )
            ).all_vals,
            {
                'a': builtins_.Int.for_value(1),
                'b': builtins_.Int.for_value(2),
            }
        )

    def test_as_child(self):
        scope = vals.Scope({'a': builtins_.Int.for_value(1)})
        self.assertIs(scope.as_child().parent, scope)


class NamespaceTest(unittest.TestCase):
    def test_members(self):
        self.assertDictEqual(
            dict(vals.Namespace(vals.Scope({
                'a': builtins_.Int.for_value(1),
                'b': builtins_.Int.for_value(2),
            })).members),
            {
                'a': builtins_.Int.for_value(1),
                'b': builtins_.Int.for_value(2),
            }
        )
