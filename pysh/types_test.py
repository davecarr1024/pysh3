'''tests for types'''

import unittest
from . import types


class TypesTest(unittest.TestCase):
    '''tests for types'''

    def test_builtins(self):
        '''tests for builtin types'''
        self.assertEqual(types.Builtin.int, types.Builtin.int)
