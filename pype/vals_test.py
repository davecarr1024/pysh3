# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from . import vals


class NoneTest(unittest.TestCase):
    def test_class(self):
        self.assertEqual('NoneClass', vals.NoneClass.name)

    def test_eq(self):
        self.assertEqual(vals.none, vals.none)


class IntTest(unittest.TestCase):
    def test_int_class(self):
        self.assertEqual('Int', vals.IntClass.name)

    def test_eq(self):
        self.assertEqual(vals.Int(value=1), vals.Int(value=1))
        self.assertNotEqual(vals.Int(value=1), vals.Int(value=2))


class ScopeTest(unittest.TestCase):
    def test_contains(self):
        self.assertIn('a', vals.Scope(None, {'a': vals.Val()}))
        self.assertNotIn('a', vals.Scope(None, {}))

    def test_get_item(self):
        self.assertEqual(
            vals.Scope(None, {'a': vals.Int(value=1)})['a'],
            vals.Int(value=1)
        )

    def test_set_item(self):
        scope = vals.Scope(None, {})
        self.assertNotIn('a', scope)
        scope['a'] = vals.Int(value=1)
        self.assertIn('a', scope)
        self.assertEqual(scope['a'], vals.Int(value=1))

    def test_vals(self):
        self.assertDictEqual(
            vals.Scope(
                vals.Scope(
                    None,
                    {
                        'a': vals.Int(value=1),
                    }
                ),
                {
                    'b': vals.Int(value=2),
                }
            ).vals,
            {
                'b': vals.Int(value=2),
            }
        )

    def test_all_vals(self):
        self.assertDictEqual(
            vals.Scope(
                vals.Scope(
                    None,
                    {
                        'a': vals.Int(value=1),
                    }
                ),
                {
                    'b': vals.Int(value=2),
                }
            ).all_vals,
            {
                'a': vals.Int(value=1),
                'b': vals.Int(value=2),
            }
        )

    def test_as_child(self):
        self.assertEqual(
            vals.Scope(None, {'a': vals.Int(value=1)}).as_child(),
            vals.Scope(vals.Scope(
                None, {'a': vals.Int(value=1)}))
        )
