# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import unittest
from . import stream


_Stream = stream.Stream[int]


class StreamTest(unittest.TestCase):

    def test_empty(self):
        self.assertTrue(_Stream([]).empty)
        self.assertFalse(_Stream([1]).empty)

    def test_head(self):
        with self.assertRaises(stream.Error):
            _ = _Stream([]).head
        self.assertEqual(_Stream([1]).head, 1)

    def test_tail(self):
        with self.assertRaises(stream.Error):
            _ = _Stream([]).tail
        self.assertEqual(
            _Stream([1, 2, 3]).tail,
            _Stream([2, 3]))
