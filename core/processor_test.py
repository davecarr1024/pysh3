from abc import ABC, abstractproperty
from dataclasses import dataclass
from typing import Generic, Tuple, TypeVar
from . import processor

import unittest

_Processor = processor.Processor[int, int]
_Result = processor.Result[int]
_ResultAndState = processor.ResultAndState[int, int]
_Rule = processor.Rule[int, int]
_State = processor.State[int, int]
_Ref = processor.Ref[int, int]
_And = processor.And[int, int]
_Or = processor.Or[int, int]
_ZeroOrMore = processor.ZeroOrMore[int, int]
_OneOrMore = processor.OneOrMore[int, int]
_ZeroOrOne = processor.ZeroOrOne[int, int]

if 'unittest.util' in __import__('sys').modules:
    # Show full diff in self.assertEqual.
    __import__('sys').modules['unittest.util']._MAX_LENGTH = 999999999


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

    def test_as_child_result(self):
        self.assertEqual(
            _Result(value=1).as_child_result(),
            _Result(children=[_Result(value=1)])
        )

    def test_empty(self):
        for input, expected in list[Tuple[_Result, bool]]([
            (_Result(), True),
            (_Result(children=[_Result()]), True),
            (_Result(children=[_Result(children=[_Result()])]), True),
        ]):
            with self.subTest(input=input, expected=expected):
                self.assertEqual(expected, input.empty())

    def test_simplify(self):
        for input, expected in list[Tuple[_Result, _Result]]([
            (_Result(value=1), _Result(value=1)),
            (_Result(rule_name='a'), _Result(rule_name='a')),
            (_Result(), _Result()),
            (_Result(children=[_Result()]), _Result()),
            (_Result(children=[_Result(children=[_Result()])]),
             _Result(children=[_Result()])),
            (_Result(children=[_Result(value=1)]), _Result(value=1)),
        ]):
            with self.subTest(input=input, expected=expected):
                actual = input.simplify()
                self.assertEqual(expected, actual)

    def test_merge_children(self):
        self.assertEqual(
            _Result.merge_children([
                _Result(children=[_Result(value=1)]),
                _Result(children=[_Result(value=2)]),
            ]),
            _Result(children=[_Result(value=1), _Result(value=2)])
        )

    def test_where_value_is(self):
        self.assertEqual(
            _Result(value=1).where(_Result.value_is(1)),
            _Result(children=[_Result(value=1)])
        )

    def test_where_has_value(self):
        self.assertEqual(
            _Result(children=[_Result(value=1), _Result(
                value=2), _Result()]).where(_Result.has_value),
            _Result(children=[_Result(value=1), _Result(value=2)])
        )

    def test_where_rule_name_is(self):
        self.assertEqual(
            _Result(rule_name='a').where(_Result.rule_name_is('a')),
            _Result(children=[_Result(rule_name='a')])
        )

    def test_all_values(self):
        self.assertSequenceEqual(
            _Result(children=[
                _Result(children=[_Result(value=1), _Result(value=2)]),
                _Result(value=3)
            ]).all_values(),
            [1, 2, 3]
        )

    def test_iter(self):
        self.assertSequenceEqual(
            [child for child in _Result(
                children=[_Result(value=1), _Result(value=2)])],
            [_Result(value=1), _Result(value=2)]
        )

    def test_getitem(self):
        self.assertEqual(
            _Result(children=[_Result(rule_name='a', value=1),
                    _Result(rule_name='b', value=2)])['b'],
            _Result(children=[_Result(rule_name='b', value=2)])
        )

    def test_len(self):
        self.assertEqual(
            len(_Result(children=[_Result(value=1), _Result(value=2)])),
            2
        )

    def test_contains(self):
        result = _Result(rule_name='a')
        self.assertIn('a', result)
        self.assertNotIn('b', result)


_ResultValue = TypeVar('_ResultValue')
_StateValue = TypeVar('_StateValue')


class ProcessorTestCase(Generic[_ResultValue, _StateValue], ABC, unittest.TestCase):
    def state(self, state_value: _StateValue) -> processor.State[_ResultValue, _StateValue]:
        return processor.State[_ResultValue, _StateValue](self.processor, state_value)

    @abstractproperty
    def processor(self) -> processor.Processor[_ResultValue, _StateValue]: ...


_ProcessorTestCase = ProcessorTestCase[int, int]


class ResultAndStateTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor('', {})

    def test_with_rule_name(self):
        self.assertEqual(
            _ResultAndState(_Result(), self.state(0)).with_rule_name('a'),
            _ResultAndState(_Result(rule_name='a'), self.state(0))
        )

    def test_as_child_result(self):
        self.assertEqual(
            _ResultAndState(_Result(value=1), self.state(0)).as_child_result(),
            _ResultAndState(_Result(value=1).as_child_result(), self.state(0))
        )


@dataclass(frozen=True)
class Multiply(_Rule):
    value: int

    def apply(self, state: _State) -> _ResultAndState:
        return _ResultAndState(_Result(value=state.value * self.value), state)


class Increment(_Rule):
    def apply(self, state: _State) -> _ResultAndState:
        return _ResultAndState(_Result(), _State(state.processor, state.value+1))


@dataclass(frozen=True)
class LessThan(_Rule):
    value: int

    def apply(self, state: _State) -> _ResultAndState:
        if state.value >= self.value:
            raise processor.Error(msg=f'{self.value} >= {state.value}')
        return _ResultAndState(_Result(), state)


class MultiplyTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': Multiply(2)})

    def test_apply(self):
        self.assertEqual(self.processor.apply_root_to_state_value(3),
                         _Result(value=6, rule_name='a'))


class IncrementTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': Increment()})

    def test_apply(self):
        self.assertEqual(self.processor.apply_root_to_state(
            self.state(1)).state.value, 2)


class LessThanTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': LessThan(1)})

    def test_apply(self):
        self.processor.apply_root_to_state_value(0)

    def test_apply_fail(self):
        with self.assertRaises(processor.Error):
            self.processor.apply_root_to_state_value(1)


class RefTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': _Ref('b'), 'b': Multiply(2)})

    def test_apply(self):
        self.assertEqual(self.processor.apply_root_to_state_value(3),
                         _Result(rule_name='a', children=[_Result(rule_name='b', value=6)]))


class AndTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _And([
                    Increment(),
                    Multiply(2),
                ]),
            }
        )

    def test_apply(self):
        self.assertEqual(
            self.processor.apply_root_to_state_value(3),
            _Result(rule_name='a', children=[_Result(value=8)])
        )


class OrTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _Or([
                    _And([
                        LessThan(3),
                        Multiply(4),
                    ]),
                    _And([
                        LessThan(4),
                        Multiply(5),
                    ]),
                ]),
            }
        )

    def test_apply(self):
        self.assertEqual(self.processor.apply_root_to_state_value(2),
                         _Result(rule_name='a', children=[
                             _Result(children=[_Result(value=8)])]))
        self.assertEqual(self.processor.apply_root_to_state_value(3),
                         _Result(rule_name='a', children=[
                             _Result(children=[_Result(value=15)])]))


class ZeroOrMoreTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _ZeroOrMore(
                    _And([
                        LessThan(3),
                        Increment(),
                        Multiply(2),
                    ]),
                ),
            }
        )

    def test_apply(self):
        self.assertEqual(self.processor.apply_root_to_state_value(1),
                         _Result(rule_name='a', children=[
                             _Result(children=[
                                     _Result(value=4)]),
                             _Result(children=[
                                 _Result(value=6)])]))
        self.assertEqual(self.processor.apply_root_to_state_value(
            10), _Result(rule_name='a'))


class OneOrMoreTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _OneOrMore(
                    _And([
                        LessThan(3),
                        Increment(),
                        Multiply(2),
                    ]),
                ),
            }
        )

    def test_apply(self):
        self.assertEqual(self.processor.apply_root_to_state_value(1),
                         _Result(rule_name='a', children=[
                             _Result(children=[
                                     _Result(value=4)]),
                             _Result(children=[
                                 _Result(value=6)])]))

    def test_apply_fail(self):
        with self.assertRaises(processor.Error):
            self.assertEqual(self.processor.apply_root_to_state_value(
                10), _Result(rule_name='a'))


class ZeroOrOneTest(_ProcessorTestCase):
    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _ZeroOrOne(
                    _And([
                        LessThan(3),
                        Increment(),
                        Multiply(2),
                    ]),
                ),
            }
        )

    def test_apply(self):
        self.assertEqual(self.processor.apply_root_to_state_value(1),
                         _Result(rule_name='a', children=[
                             _Result(children=[
                                     _Result(value=4)]),
                         ]))
        self.assertEqual(self.processor.apply_root_to_state_value(
            10), _Result(rule_name='a'))
