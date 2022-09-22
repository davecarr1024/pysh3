from . import processor

import unittest

_Result = processor.Result[int, int]
_State = processor.State[int, int]
_ResultAndState = processor.ResultAndState[int, int]
_Processor = processor.Processor[int, int]


class ErrorTest(unittest.TestCase):
    def test_with_rule_name(self):
        self.assertEqual(
            processor.Error(rule_name='a'),
            processor.Error().with_rule_name('a')
        )


class ResultTest(unittest.TestCase):
    def test_with_rule_name(self):
        self.assertEqual(
            _Result(rule_name='a'),
            _Result().with_rule_name('a'),
        )


class ResultAndStateTest(unittest.TestCase):
    def test_with_rule_name(self):
        p = _Processor('', {})
        self.assertEqual(
            _ResultAndState(_Result(), _State(p, 0)).with_rule_name('a'),
            _ResultAndState(_Result(rule_name='a'), _State(p, 0))
        )
