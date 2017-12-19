import pytest
from typing import Optional

from valid8 import validate, InputValidationError, is_even, gt, not_, is_multiple_of, or_, xor_, and_, \
    decorate_with_validation, lt, not_all, Failure, validate_arg, NonePolicy, validate_out, OutputValidationError


def test_validate_arg_nominal_builtin_validators():
    """ Simple test of the @validate_arg annotation, with built-in validators is_even and gt(1) """

    @validate_arg('a', [is_even, gt(1)])
    @validate_arg('b', is_even)
    @validate_arg('b', gt(2), none_policy=NonePolicy.SKIP)
    def myfunc(a, b = None):
        print('hello')

    # -- check that the validation works
    myfunc(84, 82)
    with pytest.raises(InputValidationError):
        # a is None
        myfunc(None, 4)
    with pytest.raises(InputValidationError):
        # a is not even
        myfunc(1, 4)
    with pytest.raises(InputValidationError):
        # a is not >= 1
        myfunc(0, 4)
    with pytest.raises(InputValidationError):
        # b is not even
        myfunc(2, 3)
    with pytest.raises(InputValidationError):
        # b is not greater than 2
        myfunc(2, 0)

    myfunc(84, None)  # None is silently skipped since the first validator for b has 'skip'


def test_validate_out():
    @validate_out([is_even, gt(1)])
    @validate_out(lt(12))
    def myfunc(x):
        return x

    myfunc(4)  # 4 is even and betwen 1 and 12
    with pytest.raises(OutputValidationError):
        myfunc(14)

    with pytest.raises(OutputValidationError):
        myfunc(0)

    with pytest.raises(OutputValidationError):
        myfunc(11)


def test_validate_nominal_builtin_validators():
    """ Simple test of the @validate annotation, with built-in validators is_even and gt(1) """

    @validate(a=[is_even, gt(1)],
              b=is_even,
              _out_=lt(100))
    def myfunc(a, b):
        print('hello')
        return a

    # -- check that the validation works
    myfunc(84, 82)
    with pytest.raises(InputValidationError):
        # a is None
        myfunc(None,0)
    with pytest.raises(InputValidationError):
        # a is not even
        myfunc(1,0)
    with pytest.raises(InputValidationError):
        # b is not even
        myfunc(2,1)
    with pytest.raises(InputValidationError):
        # a is not >= 1
        myfunc(0,0)

    with pytest.raises(OutputValidationError):
        # result is not <= 100
        myfunc(102,0)


def test_validate_custom_validators_basic():
    """ Checks that basic custom functions can be used as validators """

    def is_mod_3(x):
        """ A simple validator with no parameters"""
        return x % 3 == 0

    def is_mod(ref):
        """ A validator generator, with parameters """
        def is_mod(x):
            return x % ref == 0
        return is_mod

    def gt_assert2(x):
        """ (not recommended) A validator relying on assert and therefore only valid in 'debug' mode """
        assert x >= 2

    @validate(a=[gt_assert2, is_mod_3],
              b=is_mod(5))
    def myfunc(a, b):
        print('hello')

    # -- check that the validation works
    myfunc(21, 15)

    with pytest.raises(InputValidationError) as exc_info:
        myfunc(4, 21)  # InputValidationError: a is not a multiple of 3
    e = exc_info.value
    assert str(e) == "Error validating input [a=4] for function [myfunc]. " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [4]. " \
                     "Successes: ['gt_assert2'] / Failures: {'is_mod_3': 'False'}."

    with pytest.raises(InputValidationError) as exc_info:
        myfunc(15, 1)  # InputValidationError: b is not a multiple of 5
    e = exc_info.value
    assert str(e) == "Error validating input [b=1] for function [myfunc]: " \
                     "validation function [is_mod] returned [False]."

    with pytest.raises(InputValidationError) as exc_info:
        myfunc(1, 0)  # InputValidationError caused by AssertionError: a is not >= 2
    e = exc_info.value
    assert str(e) == "Error validating input [a=1] for function [myfunc]. " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [1]. " \
                     "Successes: [] / Failures: {'gt_assert2': 'AssertionError: assert 1 >= 2', 'is_mod_3': 'False'}."


def test_validate_custom_validators_with_exception():
    """ Checks that custom functions throwing Failure can be used as validators """

    def gt_ex1(x):
        """ A validator raising a custom exception in case of failure """
        if not x >= 1:
            raise Failure('x >= 1 does not hold for x={val}'.format(val=x))

    def is_mod(ref):
        """ A validator generator, with parameters and which raises a custom exception """
        def is_mod(x):
            if x % ref != 0:
                raise Failure('x % {ref} == 0 does not hold for x={val}'.format(ref=ref, val=x))
        return is_mod

    @validate(a=[gt_ex1, lt(12), is_mod(5)])
    def myfunc(a):
        print('hello')

    # -- check that the validation works
    myfunc(5)

    with pytest.raises(InputValidationError) as exc_info:
        print(1)
        myfunc(0)  # InputValidationError: a >= 1 does not hold
    e = exc_info.value
    assert str(e) == "Error validating input [a=0] for function [myfunc]. " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [0]. " \
                     "Successes: ['lesser_than_12', 'is_mod'] / " \
                     "Failures: {'gt_ex1': 'Failure: Wrong value: [x >= 1 does not hold for x=0]'}."

    with pytest.raises(InputValidationError) as exc_info:
        print(2)
        myfunc(3)  # InputValidationError: a % 5 == 0 does not hold
    e = exc_info.value
    assert str(e) == "Error validating input [a=3] for function [myfunc]. " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [3]. " \
                     "Successes: ['gt_ex1', 'lesser_than_12'] / " \
                     "Failures: {'is_mod': 'Failure: Wrong value: [x % 5 == 0 does not hold for x=3]'}."

    with pytest.raises(InputValidationError) as exc_info:
        print(3)
        myfunc(15)  # InputValidationError: a < 12 does not hold
    e = exc_info.value
    assert str(e) == "Error validating input [a=15] for function [myfunc]. " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [15]. " \
                     "Successes: ['gt_ex1', 'is_mod'] / " \
                     "Failures: {'lesser_than_12': 'TooBig: x <= 12 does not hold for x=15. Wrong value: [15]'}."


def test_validate_mini_lambda():
    """ Tests that mini_lambda works with @validate """

    from mini_lambda import Len, s, x, Int

    @validate(name=(0 < Len(s)) & (Len(s) <= 10),
              age=(x > 0) & (Int(x) == x))
    def hello_world(name: str, age: float):
        print('Hello, ' + name + ' your age is ' + str(age))

    hello_world('john', 20)


def test_validate_none_enforce():
    """ Tests that a None will be caught by enforce: no need for not_none validator """

    from enforce import runtime_validation, config
    from enforce.exceptions import RuntimeTypeError
    from numbers import Integral

    # we're not supposed to do that but if your python environment is a bit clunky, that might help
    config(dict(mode='covariant'))

    @runtime_validation
    @validate(a=[is_even, gt(1)], b=is_even, c=is_even)
    def myfunc(a: Integral, b: Optional[int], c=None):
        print('hello')

    # -- check that the validation works
    myfunc(84, None)     # OK because b is Nonable and c is optional with default value None
    with pytest.raises(RuntimeTypeError):
        myfunc(None, 0)  # RuntimeTypeError: a is None


def test_validate_none_pytypes():
    """ Tests that a None will be caught by pytypes: no need for not_none validator """

    from pytypes import typechecked
    from pytypes import InputTypeError
    from numbers import Integral

    # we're not supposed to do that but if your python environment is a bit clunky, that might help
    # config(dict(mode='covariant'))

    @typechecked
    @validate(a=[is_even, gt(1)], b=is_even)
    def myfunc(a: Integral, b = None):
        print('hello')

    # -- check that the validation works
    myfunc(84, None)  # OK because b has no type annotation nor not_none validator
    with pytest.raises(InputTypeError):
        myfunc(None, 0)  # InputTypeError: a is None


def test_validate_none_is_allowed():
    """ Tests that a None input is allowed by default and that in this case the validators are not executed """

    @validate(a=is_even)
    def myfunc(a = None, b = int):
        print('hello')

    # -- check that the validation works
    myfunc(84, 82)
    myfunc(None, 0)


def test_validate_name_error():
    """ Checks that wrong attribute names cant be provided to @validate"""

    with pytest.raises(ValueError):
        @validate(ab=[])
        def myfunc(a, b):
            print('hello')


def test_decorate_manually():
    """ Tests that the manual decorator works """

    def my_func(a):
        pass

    my_func = decorate_with_validation(my_func, a=is_even)

    with pytest.raises(InputValidationError):
        my_func(9)