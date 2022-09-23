from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar
import unittest
from . import processor_test, stream_processor


_Stream = stream_processor.Stream[int]
_Processor = stream_processor.Processor[int, int]
_Rule = stream_processor.Rule[int, int]
_Result = stream_processor.Result[int]
_State = stream_processor.State[int, int]
_ResultAndState = stream_processor.ResultAndState[int, int]
_UntilEmpty = stream_processor.UntilEmpty[int, int]

_ResultValue = TypeVar('_ResultValue')
_Item = TypeVar('_Item')


class StreamProcessorTestCase(Generic[_ResultValue, _Item], processor_test.ProcessorTestCase[_ResultValue, stream_processor.Stream[_Item]]):
    pass


_StreamProcessorTestCase = StreamProcessorTestCase[int, int]


class StateValueTest(unittest.TestCase):
    def test_empty(self):
        self.assertTrue(_Stream([]).empty())
        self.assertFalse(_Stream([1]).empty())

    def test_head(self):
        with self.assertRaises(stream_processor.Error):
            _Stream([]).head()
        self.assertEqual(_Stream([1]).head(), 1)

    def test_tail(self):
        with self.assertRaises(stream_processor.Error):
            _Stream([]).tail()
        self.assertEqual(
            _Stream([1, 2, 3]).tail(),
            _Stream([2, 3]))


@dataclass(frozen=True)
class Literal(stream_processor.Literal[int, int]):
    def result(self, head: int) -> _Result:
        return _Result(value=head)


class LiteralTest(_StreamProcessorTestCase):
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
            self.processor.apply_root_to_state(self.state(_Stream([1]))),
            _ResultAndState(_Result(value=1, rule_name='a'), self.state(_Stream([]))))

    def test_apply_fail(self):
        with self.assertRaises(stream_processor.Error):
            self.processor.apply_root_to_state_value(_Stream([2]))
        with self.assertRaises(stream_processor.Error):
            self.processor.apply_root_to_state_value(_Stream([]))


class UntilEmptyTest(_StreamProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': _UntilEmpty(Literal(1))})

    def test_apply(self):
        self.assertEqual(
            self.processor.apply_root_to_state_value(_Stream([1, 1, 1])),
            _Result(rule_name='a', children=[
                    _Result(value=1), _Result(value=1), _Result(value=1)])
        )

    def test_apply_fail(self):
        for values in list[Sequence[int]]([
            [1, 1, 1, 2],
            [2],
        ]):
            with self.subTest(input=values):
                with self.assertRaises(stream_processor.Error):
                    self.processor.apply_root_to_state_value(
                        _Stream(values))
