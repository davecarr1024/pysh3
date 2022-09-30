# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from pype import builtins_, vals


class ScopeTest(unittest.TestCase):
    def test_contains(self):
        self.assertIn('a', vals.Scope(None, {'a': vals.Val()}))
        self.assertNotIn('a', vals.Scope(None, {}))

    def test_get_item(self):
        self.assertEqual(
            vals.Scope(None, {'a': builtins_.Int(value=1)})['a'],
            builtins_.Int(value=1)
        )

    def test_set_item(self):
        scope = vals.Scope(None, {})
        self.assertNotIn('a', scope)
        scope['a'] = builtins_.Int(value=1)
        self.assertIn('a', scope)
        self.assertEqual(scope['a'], builtins_.Int(value=1))

    def test_vals(self):
        self.assertDictEqual(
            vals.Scope(
                vals.Scope(
                    None,
                    {
                        'a': builtins_.Int(value=1),
                    }
                ),
                {
                    'b': builtins_.Int(value=2),
                }
            ).vals,
            {
                'b': builtins_.Int(value=2),
            }
        )

    def test_all_vals(self):
        self.assertDictEqual(
            vals.Scope(
                vals.Scope(
                    None,
                    {
                        'a': builtins_.Int(value=1),
                    }
                ),
                {
                    'b': builtins_.Int(value=2),
                }
            ).all_vals,
            {
                'a': builtins_.Int(value=1),
                'b': builtins_.Int(value=2),
            }
        )

    def test_as_child(self):
        self.assertEqual(
            vals.Scope(None, {'a': builtins_.Int(value=1)}).as_child(),
            vals.Scope(vals.Scope(
                None, {'a': builtins_.Int(value=1)}))
        )
