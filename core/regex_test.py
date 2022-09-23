import unittest

from . import regex
from . import processor_test


class CharTest(unittest.TestCase):
    def test_ctor(self):
        regex.Char('a')

    def test_ctor_fail(self):
        with self.assertRaises(regex.Error):
            regex.Char('')
        with self.assertRaises(regex.Error):
            regex.Char('aa')


_ProcessorTest = processor_test.ProcessorTestCase[regex.Char, regex.CharStream]


class LiteralTest(_ProcessorTest):
    @property
    def processor(self) -> regex.Regex:
        return regex.Regex('a', {'a': regex.Literal(regex.Char('a'))})

    def test_apply(self):
        self.assertEqual(self.processor.apply('a'), 'a')

    def test_apply_fail(self):
        with self.assertRaises(regex.Error):
            self.processor.apply('b')
