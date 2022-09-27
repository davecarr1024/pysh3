'''test for stream_processor'''

from dataclasses import dataclass
from typing import Generic, Sequence, Tuple, TypeVar
import unittest
from . import processor_test, stream_processor


_Stream = stream_processor.Stream[int]
_Processor = stream_processor.Processor[int, int]
_Result = stream_processor.Result[int]
_ResultAndState = stream_processor.ResultAndState[int, int]
_UntilEmpty = stream_processor.UntilEmpty[int, int]

_ResultValue = TypeVar('_ResultValue')
_Item = TypeVar('_Item')


class StreamProcessorTestCase(
    Generic[_ResultValue, _Item],
    processor_test.ProcessorTestCase[_ResultValue,
                                     stream_processor.Stream[_Item]],
):
    '''generic test case for use on stream processors'''


_StreamProcessorTestCase = StreamProcessorTestCase[int, int]


class StreamTest(unittest.TestCase):
    '''tests for stream_processor.Stream'''

    def test_empty(self):
        '''tests for stream_processor.Stream.empty'''
        self.assertTrue(_Stream([]).empty)
        self.assertFalse(_Stream([1]).empty)

    def test_head(self):
        '''tests for stream_processor.Stream.head'''
        with self.assertRaises(stream_processor.Error):
            _ = _Stream([]).head
        self.assertEqual(_Stream([1]).head, 1)

    def test_tail(self):
        '''tests for stream_processor.Stream.tail'''
        with self.assertRaises(stream_processor.Error):
            _ = _Stream([]).tail
        self.assertEqual(
            _Stream([1, 2, 3]).tail,
            _Stream([2, 3]))


@dataclass(frozen=True)
class _Literal(stream_processor.Literal[int, int]):
    def result(self, head: int) -> _Result:
        return _Result(value=head)


class LiteralTest(_StreamProcessorTestCase):
    '''tests for _Literal'''

    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _Literal(1),
            }
        )

    def test_apply(self):
        '''tests for _Literal.apply'''
        self.assertEqual(
            self.processor.apply_root_to_state(self.state(_Stream([1]))),
            _ResultAndState(_Result(value=1, rule_name='a'), self.state(_Stream([]))))

    def test_apply_fail(self):
        '''tests for _Literal.apply failures'''
        for values, expected_error in list[Tuple[Sequence[int], stream_processor.Error]]([
            ([], stream_processor.StateError(
                msg='failed _Literal(value=1): empty stream', state_value=_Stream([]))),
            ([2], stream_processor.StateError(
                msg='failed _Literal(value=1)', state_value=_Stream([2]))),
        ]):
            with self.subTest(values=values, expected_error=expected_error):
                with self.assertRaises(stream_processor.Error) as ctx:
                    self.processor.apply_root_to_state_value(_Stream(values))
                self.assertEqual(expected_error, ctx.exception)


class UntilEmptyTest(_StreamProcessorTestCase):
    '''tests for stream_processor.UntilEmpty'''

    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': _UntilEmpty(_Literal(1))})

    def test_apply(self):
        '''tests for stream_processor.UntilEmpty.apply'''
        self.assertEqual(
            self.processor.apply_root_to_state_value(_Stream([1, 1, 1])),
            _Result(rule_name='a', children=[
                    _Result(value=1), _Result(value=1), _Result(value=1)])
        )

    def test_apply_fail(self):
        '''tests for stream_processor.UntilEmpty.apply failures'''
        for values in list[Sequence[int]]([
            [1, 1, 1, 2],
            [2],
        ]):
            with self.subTest(input=values):
                with self.assertRaises(stream_processor.Error):
                    self.processor.apply_root_to_state_value(
                        _Stream(values))
