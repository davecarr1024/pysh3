'''tests for processor'''

import unittest

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Tuple, TypeVar
from . import processor

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
    # pylint: disable=protected-access
    __import__(
        'sys').modules['unittest.util']._MAX_LENGTH = 999999999
    # pylint: enable=protected-access


class ErrorTest(unittest.TestCase):
    '''tests for processor.Error'''

    def test_with_rule_name(self):
        '''test for processor.Error.with_rule_name'''
        self.assertEqual(
            processor.Error(rule_name='a'),
            processor.Error().with_rule_name('a')
        )


class ResultTest(unittest.TestCase):
    '''tests for processor.Result'''

    def test_with_rule_name(self):
        '''tests for processor.Result.with_rule_name'''
        self.assertEqual(
            _Result(rule_name='a'),
            _Result().with_rule_name('a'),
        )

    def test_as_child_result(self):
        '''tests for processor.Result.as_child_result'''
        self.assertEqual(
            _Result(value=1).as_child_result(),
            _Result(children=[_Result(value=1)])
        )

    def test_empty(self):
        '''tests for processor.Result.empty'''
        for result, expected in list[Tuple[_Result, bool]]([
            (_Result(), True),
            (_Result(children=[_Result()]), True),
            (_Result(children=[_Result(children=[_Result()])]), True),
        ]):
            with self.subTest(input=result, expected=expected):
                self.assertEqual(expected, result.empty())

    def test_simplify(self):
        '''tests for processor.Result.simplify'''
        for result, expected in list[Tuple[_Result, _Result]]([
            (_Result(value=1), _Result(value=1)),
            (_Result(rule_name='a'), _Result(rule_name='a')),
            (_Result(), _Result()),
            (_Result(children=[_Result()]), _Result()),
            (_Result(children=[_Result(children=[_Result()])]),
             _Result(children=[_Result()])),
            (_Result(children=[_Result(value=1)]), _Result(value=1)),
        ]):
            with self.subTest(input=result, expected=expected):
                actual = result.simplify()
                self.assertEqual(expected, actual)

    def test_merge_children(self):
        '''tests for processor.Result.merge_children'''
        self.assertEqual(
            _Result.merge_children([
                _Result(children=[_Result(value=1)]),
                _Result(children=[_Result(value=2)]),
            ]),
            _Result(children=[_Result(value=1), _Result(value=2)])
        )

    def test_where_value_is(self):
        '''tests for processor.Result.where with value_is'''
        self.assertEqual(
            _Result(value=1).where(_Result.value_is(1)),
            _Result(children=[_Result(value=1)])
        )

    def test_where_has_value(self):
        '''tests for processor.Result.where with has_value'''
        self.assertEqual(
            _Result(children=[_Result(value=1), _Result(
                value=2), _Result()]).where(_Result.has_value),
            _Result(children=[_Result(value=1), _Result(value=2)])
        )

    def test_where_rule_name_is(self):
        '''tests for processor.Result.where with rule_name_is'''
        self.assertEqual(
            _Result(rule_name='a').where(_Result.rule_name_is('a')),
            _Result(children=[_Result(rule_name='a')])
        )

    def test_where_rule_name_in(self):
        '''tests for processor.Result.where with rule_name_in'''
        self.assertEqual(
            _Result(rule_name='a').where(_Result.rule_name_in(('a', 'b'))),
            _Result(children=[_Result(rule_name='a')])
        )

    def test_where_n(self):
        '''verify where_n returns n matching results'''
        self.assertEqual(
            _Result(children=[
                _Result(rule_name='a', value=1),
                _Result(rule_name='a', value=2),
                _Result(rule_name='b', value=3),
            ]).where_n(_Result.rule_name_is('a'), 2),
            _Result(children=[
                _Result(rule_name='a', value=1),
                _Result(rule_name='a', value=2),
            ])
        )

    def test_where_n_empty(self):
        '''where_n returns error when there aren't enough matching results'''
        with self.assertRaises(processor.Error):
            _Result(children=[]).where_n(_Result.rule_name_is('a'), 2)

    def test_where_n_too_many(self):
        '''where_n returns error when there are too many matching results'''
        with self.assertRaises(processor.Error):
            _Result(children=[
                _Result(rule_name='a', value=1),
                _Result(rule_name='a', value=2),
                _Result(rule_name='a', value=3),
            ]).where_n(_Result.rule_name_is('a'), 2)

    def test_where_one(self):
        '''where one returns exactly one matching result (not nested)'''
        self.assertEqual(
            _Result(children=[
                _Result(rule_name='a', value=1),
                _Result(rule_name='b', value=2),
            ]).where_one(_Result.rule_name_is('a')),
            _Result(rule_name='a', value=1)
        )

    def test_where_one_empty(self):
        '''where_one fails on empty input'''
        with self.assertRaises(processor.Error):
            _Result(children=[]).where_one(_Result.rule_name_is('a'))

    def test_where_one_too_many(self):
        '''where_one fails on too many matches'''
        with self.assertRaises(processor.Error):
            _Result(children=[
                _Result(rule_name='a', value=1),
                _Result(rule_name='a', value=2),
            ]).where_one(_Result.rule_name_is('a'))

    def test_all_values(self):
        '''all_values returns all values in result tree'''
        self.assertSequenceEqual(
            _Result(children=[
                _Result(children=[_Result(value=1), _Result(value=2)]),
                _Result(value=3)
            ]).all_values(),
            [1, 2, 3]
        )

    def test_iter(self):
        '''verify result children are iterable'''
        self.assertSequenceEqual(
            list(_Result(
                children=[_Result(value=1), _Result(value=2)])),
            [_Result(value=1), _Result(value=2)]
        )

    def test_getitem(self):
        '''result[foo] returns all children of rule_name=foo'''
        self.assertEqual(
            _Result(children=[_Result(rule_name='a', value=1),
                    _Result(rule_name='b', value=2)])['b'],
            _Result(children=[_Result(rule_name='b', value=2)])
        )

    def test_len(self):
        '''len return length of result children'''
        self.assertEqual(
            len(_Result(children=[_Result(value=1), _Result(value=2)])),
            2
        )

    def test_contains(self):
        '''in returns if any child has the given rule_name'''
        result = _Result(rule_name='a')
        self.assertIn('a', result)
        self.assertNotIn('b', result)


_ResultValue = TypeVar('_ResultValue')
_StateValue = TypeVar('_StateValue')


class ProcessorTestCase(
    Generic[_ResultValue, _StateValue],
    ABC,
    unittest.TestCase,
):
    '''generic processor test case'''

    def state(
        self,
        state_value: _StateValue
    ) -> processor.State[_ResultValue, _StateValue]:
        '''create a state with this test's processor'''
        return processor.State[_ResultValue, _StateValue](
            self.processor,
            state_value
        )

    @property
    @abstractmethod
    def processor(self) -> processor.Processor[_ResultValue, _StateValue]:
        '''the generic processor to be used for all tests'''


_ProcessorTestCase = ProcessorTestCase[int, int]


class ResultAndStateTest(_ProcessorTestCase):
    '''tests for processor.ResultAndState'''

    @property
    def processor(self) -> _Processor:
        return _Processor('', {})

    def test_with_rule_name(self):
        '''test for processor.ResultAndState.with_rule_name'''
        self.assertEqual(
            _ResultAndState(_Result(), self.state(0)).with_rule_name('a'),
            _ResultAndState(_Result(rule_name='a'), self.state(0))
        )

    def test_as_child_result(self):
        '''test for processor.ResultAndState.as_child_result'''
        self.assertEqual(
            _ResultAndState(_Result(value=1), self.state(0)).as_child_result(),
            _ResultAndState(_Result(value=1).as_child_result(), self.state(0))
        )


@dataclass(frozen=True)
class _Multiply(_Rule):
    value: int

    def apply(self, state: _State) -> _ResultAndState:
        return _ResultAndState(_Result(value=state.value * self.value), state)


class _Increment(_Rule):  # pylint: disable=too-few-public-methods
    def apply(self, state: _State) -> _ResultAndState:
        return _ResultAndState(
            _Result(),
            _State(
                state.processor,
                state.value+1
            )
        )


@dataclass(frozen=True)
class _LessThan(_Rule):
    value: int

    def apply(self, state: _State) -> _ResultAndState:
        if state.value >= self.value:
            raise processor.Error(msg=f'{self.value} >= {state.value}')
        return _ResultAndState(_Result(), state)


class MultiplyTest(_ProcessorTestCase):
    '''test behavior of _Multiply rule'''

    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': _Multiply(2)})

    def test_apply(self):
        '''test _Multiply.apply multiplies state by result'''
        self.assertEqual(self.processor.apply_root_to_state_value(3),
                         _Result(value=6, rule_name='a'))


class IncrementTest(_ProcessorTestCase):
    '''test for _Increment'''
    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': _Increment()})

    def test_apply(self):
        '''_Increment.apply increments state'''
        self.assertEqual(self.processor.apply_root_to_state(
            self.state(1)).state.value, 2)


class LessThanTest(_ProcessorTestCase):
    '''test for _LessThan rule'''

    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': _LessThan(1)})

    def test_apply(self):
        '''apply verifies state < value'''
        self.processor.apply_root_to_state_value(0)

    def test_apply_fail(self):
        '''apply fails when state >= value'''
        with self.assertRaises(processor.Error):
            self.processor.apply_root_to_state_value(1)


class RefTest(_ProcessorTestCase):
    '''tests for processor.Ref'''
    @property
    def processor(self) -> _Processor:
        return _Processor('a', {'a': _Ref('b'), 'b': _Multiply(2)})

    def test_apply(self):
        '''apply looks up a rule and applies it'''
        self.assertEqual(
            self.processor.apply_root_to_state_value(3),
            _Result(rule_name='a', children=[_Result(rule_name='b', value=6)])
        )


class AndTest(_ProcessorTestCase):
    '''tests for processor.And'''

    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _And([
                    _Increment(),
                    _Multiply(2),
                ]),
            }
        )

    def test_apply(self):
        '''apply applies all rules in sequence'''
        self.assertEqual(
            self.processor.apply_root_to_state_value(3),
            _Result(rule_name='a', children=[_Result(value=8)])
        )


class OrTest(_ProcessorTestCase):
    '''tests for processor.Or'''

    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _Or([
                    _And([
                        _LessThan(3),
                        _Multiply(4),
                    ]),
                    _And([
                        _LessThan(4),
                        _Multiply(5),
                    ]),
                ]),
            }
        )

    def test_apply(self):
        '''tests for processor.Or.apply'''
        self.assertEqual(self.processor.apply_root_to_state_value(2),
                         _Result(rule_name='a', children=[
                             _Result(children=[_Result(value=8)])]))
        self.assertEqual(self.processor.apply_root_to_state_value(3),
                         _Result(rule_name='a', children=[
                             _Result(children=[_Result(value=15)])]))


class ZeroOrMoreTest(_ProcessorTestCase):
    '''tests for processor.ZeroOrMore'''
    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _ZeroOrMore(
                    _And([
                        _LessThan(3),
                        _Increment(),
                        _Multiply(2),
                    ]),
                ),
            }
        )

    def test_apply(self):
        '''tests for processor.ZeroOrMore.apply'''
        self.assertEqual(self.processor.apply_root_to_state_value(1),
                         _Result(rule_name='a', children=[
                             _Result(children=[
                                     _Result(value=4)]),
                             _Result(children=[
                                 _Result(value=6)])]))
        self.assertEqual(self.processor.apply_root_to_state_value(
            10), _Result(rule_name='a'))


class OneOrMoreTest(_ProcessorTestCase):
    '''tests for processor.OneOrMore'''

    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _OneOrMore(
                    _And([
                        _LessThan(3),
                        _Increment(),
                        _Multiply(2),
                    ]),
                ),
            }
        )

    def test_apply(self):
        '''tests for processor.OneOrMore.apply'''
        self.assertEqual(self.processor.apply_root_to_state_value(1),
                         _Result(rule_name='a', children=[
                             _Result(children=[
                                     _Result(value=4)]),
                             _Result(children=[
                                 _Result(value=6)])]))

    def test_apply_fail(self):
        '''tests for processor.OneOrMore.apply failures'''
        with self.assertRaises(processor.Error):
            self.assertEqual(self.processor.apply_root_to_state_value(
                10), _Result(rule_name='a'))


class ZeroOrOneTest(_ProcessorTestCase):
    '''tests for processor.ZeroOrOne'''

    @property
    def processor(self) -> _Processor:
        return _Processor(
            'a',
            {
                'a': _ZeroOrOne(
                    _And([
                        _LessThan(3),
                        _Increment(),
                        _Multiply(2),
                    ]),
                ),
            }
        )

    def test_apply(self):
        '''tests for processor.ZeroOrOne.apply'''
        self.assertEqual(self.processor.apply_root_to_state_value(1),
                         _Result(rule_name='a', children=[
                             _Result(children=[
                                     _Result(value=4)]),
                         ]))
        self.assertEqual(self.processor.apply_root_to_state_value(
            10), _Result(rule_name='a'))
