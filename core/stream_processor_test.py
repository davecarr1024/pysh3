from dataclasses import dataclass
import unittest
from . import processor_test, stream_processor


_Item = int
_ResultValue = int

_StateValue = stream_processor.Stream[_Item]
_Processor = stream_processor.Processor[_ResultValue, _Item]
_Rule = stream_processor.Rule[_ResultValue, _Item]
_Result = stream_processor.Result[_ResultValue]
_State = stream_processor.State[_ResultValue, _Item]
_ResultAndState = stream_processor.ResultAndState[_ResultValue, _Item]
_ProcessorTestCase = processor_test.ProcessorTestCase[_ResultValue, _StateValue]
_UntilEmpty = stream_processor.UntilEmpty[_ResultValue, _Item]


class StateValueTest(unittest.TestCase):
    def test_empty(self):
        self.assertTrue(_StateValue([]).empty())
        self.assertFalse(_StateValue([1]).empty())

    def test_head(self):
        with self.assertRaises(stream_processor.Error):
            _StateValue([]).head()
        self.assertEqual(_StateValue([1]).head(), 1)

    def test_tail(self):
        with self.assertRaises(stream_processor.Error):
            _StateValue([]).tail()
        self.assertEqual(
            _StateValue([1, 2, 3]).tail(),
            _StateValue([2, 3]))


@dataclass(frozen=True)
class Literal(stream_processor.Literal[_ResultValue, _Item]):
    def result(self, head: _Item) -> _Result:
        return _Result(value=head)


class LiteralTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': Literal(1),
            }
        )

    def test_apply(self):
        self.assertEqual(
            self.processor.apply_root_to_state(self.state(_StateValue([1]))),
            _ResultAndState(_Result(value=1, rule_name='a'), self.state(_StateValue([]))))

    def test_apply_fail(self):
        with self.assertRaises(stream_processor.Error):
            self.processor.apply_root_to_state_value(_StateValue([2]))
        with self.assertRaises(stream_processor.Error):
            self.processor.apply_root_to_state_value(_StateValue([]))


class UntilEmptyTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': _UntilEmpty(Literal(1))})

    def test_apply(self):
        self.assertEqual(
            self.processor.apply_root_to_state_value(_StateValue([1, 1, 1])),
            _Result(rule_name='a', children=[
                    _Result(value=1), _Result(value=1), _Result(value=1)])
        )

    def test_apply_fail(self):
        with self.assertRaises(stream_processor.Error):
            self.processor.apply_root_to_state_value(_StateValue([1, 1, 1, 2]))
