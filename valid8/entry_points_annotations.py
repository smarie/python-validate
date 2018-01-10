from inspect import signature, Signature

from typing import Callable, Any, List, Type, Union

from decorator import decorate

from valid8.utils_typing import is_pep484_nonable
from valid8.utils_decoration import create_function_decorator__robust_to_args, apply_on_each_func_args_sig
from valid8.base import get_callable_name
from valid8.composition import ValidationFuncs
from valid8.entry_points import ValidationError, Validator, NonePolicy, NoneArgPolicy


class InputValidationError(ValidationError):
    """
    Exception raised whenever function input validation fails. It is almost identical to `ValidationError`, except that
    the inner validator is a `InputValidator`, which provides more contextual information to display.

    Users may (recommended) subclass this type the same way they do for `ValidationError`, so as to generate unique
    error codes for their applications.

    See `ValidationError` for details.
    """

    def get_what_txt(self):
        """
        Overrides the base behaviour defined in ValidationError in order to add details about the function.
        :return:
        """
        return 'input [{var}] for function [{func}]'.format(var=self.get_variable_str(),
                                                            func=self.validator.get_validated_func_display_name())


class OutputValidationError(ValidationError):
    """
    Exception raised whenever function output validation fails. It is almost identical to `ValidationError`, except that
    the inner validator is an `OutputValidator`, which provides more contextual information to display.

    Users may (recommended) subclass this type the same way they do for `ValidationError`, so as to generate unique
    error codes for their applications.

    See `ValidationError` for details.
    """

    def get_what_txt(self):
        """
        Overrides the base behaviour defined in ValidationError in order to add details about the function.
        :return:
        """
        return 'output of function [{func}]'.format(func=self.validator.get_validated_func_display_name())


class FuncValidator(Validator):
    """
    Represents a special kind of `Validator` responsible to validate a function input or output
    """

    def __init__(self, validated_func: Callable, *validation_func: ValidationFuncs,
                 error_type: Type[InputValidationError] = None, help_msg: str = None, none_policy: int = None,
                 **kw_context_args):
        """

        :param validated_func: the function whose input is being validated.
        :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
        are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
        `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
        :param error_type: a subclass of ValidationError to raise in case of validation failure. By default a
        ValidationError will be raised with the provided help_msg
        :param help_msg: an optional help message to be used in the raised error in case of validation failure.
        :param none_policy: describes how None values should be handled. See `NonePolicy` for the various possibilities.
        Default is `NonePolicy.VALIDATE`, meaning that None values will be treated exactly like other values and follow
        the same validation process.
        :param kw_context_args: optional contextual information to store in the exception, and that may be also used
        to format the help message
        """

        # store this additional info about the function been validated
        self.validated_func = validated_func

        super(FuncValidator, self).__init__(*validation_func, none_policy=none_policy,
                                            error_type=error_type, help_msg=help_msg, **kw_context_args)

    def get_additional_info_for_repr(self):
        return 'validated_function={func}'.format(func=get_callable_name(self.validated_func))

    def get_validated_func_display_name(self):
        """
        Utility method to get a friendly display name for the function being validated by this FuncValidator
        :return:
        """
        return self.validated_func.__name__ or str(self.validated_func)


class InputValidator(FuncValidator):
    """
    Represents a special kind of `Validator` responsible to validate a function input.
    """

    def __init__(self, validated_func: Callable, *validation_func: ValidationFuncs,
                 error_type: Type[InputValidationError] = None, help_msg: str = None, none_policy: int = None,
                 **kw_context_args):
        """

        :param validated_func: the function whose input is being validated.
        :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
        are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
        `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
        :param error_type: a subclass of ValidationError to raise in case of validation failure. By default a
        ValidationError will be raised with the provided help_msg
        :param help_msg: an optional help message to be used in the raised error in case of validation failure.
        :param none_policy: describes how None values should be handled. See `NonePolicy` for the various possibilities.
        Default is `NonePolicy.VALIDATE`, meaning that None values will be treated exactly like other values and follow
        the same validation process.
        :param kw_context_args: optional contextual information to store in the exception, and that may be also used
        to format the help message
        """

        # super constructor with default error type 'InputValidationError'
        error_type = error_type or InputValidationError
        if not issubclass(error_type, InputValidationError):
            raise ValueError('error_type should be a subclass of InputValidationError, found ' + str(error_type))

        super(InputValidator, self).__init__(validated_func, *validation_func, none_policy=none_policy,
                                             error_type=error_type, help_msg=help_msg, **kw_context_args)


class OutputValidator(FuncValidator):
    """ Represents a special kind of `Validator` responsible to validate a function output. """

    def __init__(self, validated_func: Callable, *validation_func: ValidationFuncs,
                 error_type: Type[OutputValidationError] = None, help_msg: str = None, none_policy: int = None,
                 **kw_context_args):
        """

        :param validated_func: the function whose input is being validated.
        :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
        are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
        `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
        :param error_type: a subclass of ValidationError to raise in case of validation failure. By default a
        ValidationError will be raised with the provided help_msg
        :param help_msg: an optional help message to be used in the raised error in case of validation failure.
        :param none_policy: describes how None values should be handled. See `NonePolicy` for the various possibilities.
        Default is `NonePolicy.VALIDATE`, meaning that None values will be treated exactly like other values and follow
        the same validation process.
        :param kw_context_args: optional contextual information to store in the exception, and that may be also used
        to format the help message
        """
        # store this additional info
        self.validated_func = validated_func

        # super constructor with default error type 'InputValidationError'
        error_type = error_type or OutputValidationError
        if not issubclass(error_type, OutputValidationError):
            raise ValueError('error_type should be a subclass of OutputValidationError, found ' + str(error_type))

        super(OutputValidator, self).__init__(validated_func, *validation_func, none_policy=none_policy,
                                              error_type=error_type, help_msg=help_msg, **kw_context_args)

    def __call__(self, value: Any, error_type: Type[ValidationError] = None, help_msg: str = None, **kw_context_args):
        super(OutputValidator, self).__call__('result', value, error_type=error_type, help_msg=help_msg,
                                              **kw_context_args)

    def assert_valid(self, value: Any, error_type: Type[ValidationError] = None,
                     help_msg: str = None, **kw_context_args):
        super(OutputValidator, self).assert_valid('result', value, error_type=error_type, help_msg=help_msg,
                                                  **kw_context_args)


def validate(none_policy: int=None, _out_: ValidationFuncs=None, **kw_validation_funcs: ValidationFuncs):
    """
    A function decorator to add input validation prior to the function execution. It should be called with named
    arguments: for each function arg name, provide a single validation function or a list of validation functions to
    apply. If validation fails, it will raise an InputValidationError with details about the function, the input name,
    and any further information available from the validation function(s)

    For example:

    ```
    def is_even(x):
        return x % 2 == 0

    def gt(a):
        def gt(x):
            return x >= a
        return gt

    @validate(a=[is_even, gt(1)], b=is_even)
    def myfunc(a, b):
        print('hello')
    ```

    will generate the equivalent of :

    ```
    def myfunc(a, b):
        gt1 = gt(1)
        if (is_even(a) and gt1(a)) and is_even(b):
            print('hello')
        else:
            raise InputValidationError(...)
    ```

    :param none_policy: describes how None values should be handled. See `NoneArgPolicy` for the various
    possibilities. Default is `NoneArgPolicy.ACCEPT_IF_OPTIONAl_ELSE_VALIDATE`.
    :param _out_: a validation function or list of validation functions to apply to the function output. See
    kw_validation_funcs for details about the syntax.
    :param kw_validation_funcs: keyword arguments: for each of the function's input names, the validation function or
    list of validation functions to use. A validation function may be a callable, a tuple(callable, help_msg_str),
    a tuple(callable, failure_type), or a list of several such elements. Nested lists are supported and indicate an
    implicit `and_` (such as the main list). Tuples indicate an implicit `_failure_raiser`.
    [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of callables, they will
    be transformed to functions automatically.
    :return: the decorated function, that will perform input validation before executing the function's code everytime
    it is executed.
    """

    # this is a general technique for decorators, to properly handle both cases of being called with arguments or not
    # this is really not needed in our case since @validate will never be used as is (without a call), but it does not
    # cost much and may be of interest in the future

    return create_function_decorator__robust_to_args(decorate_several_with_validation, none_policy=none_policy,
                                                     _out_=_out_, **kw_validation_funcs)


alidate = validate
""" an alias for the @validate decorator, to use as follows : import valid8 as v : @v.alidate(...) """


def validate_arg(arg_name, *validation_func: ValidationFuncs, help_msg: str = None,
                 error_type: Type[InputValidationError] = None, none_policy: int = None, **kw_context_args) -> Callable:
    """
    A decorator to apply function input validation for the given argument name, with the provided base validation
    function(s). You may use several such decorators on a given function as long as they are stacked on top of each
    other (no external decorator in the middle)

    :param arg_name:
    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param error_type: a subclass of ValidationError to raise in case of validation failure. By default a
    ValidationError will be raised with the provided help_msg
    :param help_msg: an optional help message to be used in the raised error in case of validation failure.
    :param none_policy: describes how None values should be handled. See `NoneArgPolicy` for the various
    possibilities. Default is `NoneArgPolicy.ACCEPT_IF_OPTIONAl_ELSE_VALIDATE`.
    :param kw_context_args: optional contextual information to store in the exception, and that may be also used
    to format the help message
    :return: a function decorator, able to transform a function into a function that will perform input validation
    before executing the function's code everytime it is executed.
    """
    # this is a general technique for decorators, to properly handle both cases of being called with arguments or not
    # this is really not needed in our case since @validate will never be used as is (without a call), but it does not
    # cost much and may be of interest in the future
    return create_function_decorator__robust_to_args(decorate_with_validation, arg_name,
                                                     *validation_func,
                                                     help_msg=help_msg, error_type=error_type, none_policy=none_policy,
                                                     **kw_context_args)


def validate_out(*validation_func: ValidationFuncs, help_msg: str = None,
                 error_type: Type[OutputValidationError] = None, none_policy: int = None, **kw_context_args) \
        -> Callable:
    """
    A decorator to apply function output validation to this function's output, with the provided base validation
    function(s). You may use several such decorators on a given function as long as they are stacked on top of each
    other (no external decorator in the middle)

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param none_policy: describes how None values should be handled. See `NoneArgPolicy` for the various
    possibilities. Default is `NoneArgPolicy.ACCEPT_IF_OPTIONAl_ELSE_VALIDATE`.
    :return: a function decorator, able to transform a function into a function that will perform input validation
    before executing the function's code everytime it is executed.
    """
    # this is a general technique for decorators, to properly handle both cases of being called with arguments or not
    # this is really not needed in our case since @validate will never be used as is (without a call), but it does not
    # cost much and may be of interest in the future
    return create_function_decorator__robust_to_args(decorate_with_validation, _OUT_KEY,
                                                     *validation_func,
                                                     help_msg=help_msg, error_type=error_type, none_policy=none_policy,
                                                     **kw_context_args)


def _get_final_none_policy_for_validator(is_nonable, none_policy):
    if none_policy in {NonePolicy.VALIDATE, NonePolicy.SKIP, NonePolicy.FAIL}:
        none_policy_to_use = none_policy

    elif none_policy is NoneArgPolicy.SKIP_IF_NONABLE_ELSE_VALIDATE:
        none_policy_to_use = NonePolicy.SKIP if is_nonable else NonePolicy.VALIDATE

    elif none_policy is NoneArgPolicy.SKIP_IF_NONABLE_ELSE_FAIL:
        none_policy_to_use = NonePolicy.SKIP if is_nonable else NonePolicy.FAIL

    else:
        raise ValueError('Invalid none policy: ' + str(none_policy))
    return none_policy_to_use


_OUT_KEY = '_out_'
""" The reserved key for output validation """


def _create_function_validator(validated_func: Callable, s: Signature, arg_name: str,
                               *validation_func: ValidationFuncs, help_msg: str = None,
                               error_type: Type[InputValidationError] = None, none_policy: int = None,
                               **kw_context_args):

    # if the function is a valid8 wrapper, rather refer to the __wrapped__ function.
    if hasattr(validated_func, '__wrapped__') and hasattr(validated_func.__wrapped__, '__validators__'):
        validated_func = validated_func.__wrapped__

    # check that provided input/output name is correct
    if arg_name not in s.parameters and arg_name is not _OUT_KEY:
        raise ValueError('@validate definition exception: argument name \''
                         + str(arg_name) + '\' is not part of signature for ' + str(validated_func)
                         + ' and is not ' + _OUT_KEY)

    # create the new Validator object according to the none_policy and function signature
    if arg_name is not _OUT_KEY:
        # first check which none policy we should adopt according to the arg annotations
        is_nonable = (s.parameters[arg_name].default is None) or is_pep484_nonable(s.parameters[arg_name].annotation)
        none_policy_to_use = _get_final_none_policy_for_validator(is_nonable, none_policy)
        # then create
        return InputValidator(validated_func, *validation_func, none_policy=none_policy_to_use,
                              error_type=error_type, help_msg=help_msg, **kw_context_args)
    else:
        # first check which none policy we should adopt according to the arg annotations
        is_nonable = is_pep484_nonable(s.return_annotation)
        none_policy_to_use = _get_final_none_policy_for_validator(is_nonable, none_policy)
        # then create
        return OutputValidator(validated_func, *validation_func, none_policy=none_policy_to_use,
                               error_type=error_type, help_msg=help_msg, **kw_context_args)


def decorate_several_with_validation(func, _out_: ValidationFuncs = None, none_policy: int = None,
                                     **validation_funcs: ValidationFuncs) -> Callable:
    """
    This method is equivalent to applying `decorate_with_validation` once for each of the provided arguments of
    the function `func` as well as output `_out_`. validation_funcs keyword arguments are validation functions for each
    arg name.

    Note that this method is less flexible than decorate_with_validation since
     * it does not allow to associate a custom error message or error type with each validation.
     * the none_policy is the same for all inputs and outputs

    :param func:
    :param _out_:
    :param validation_funcs:
    :param none_policy:
    :return: a function decorated with validation for all of the listed arguments and output if provided.
    """

    # add validation for output if provided
    if _out_ is not None:
        func = decorate_with_validation(func, _OUT_KEY, _out_, none_policy=none_policy)

    # add validation for each of the listed arguments
    for att_name, att_validation_funcs in validation_funcs.items():
        func = decorate_with_validation(func, att_name, att_validation_funcs, none_policy=none_policy)

    return func


def decorate_with_validation(func, arg_name, *validation_func: ValidationFuncs, help_msg: str = None,
                             error_type: Union[Type[InputValidationError], Type[OutputValidationError]] = None,
                             none_policy: int = None, **kw_context_args) -> Callable:
    """
    This method is equivalent to decorating a function with the `@validate`, `@validate_arg` or `@validate_out`
    decorators, but can be used a posteriori.


    :param func:
    :param arg_name: the name of the argument to validate or _OUT_KEY for output validation
    :param validation_func: the validation function or
    list of validation functions to use. A validation function may be a callable, a tuple(callable, help_msg_str),
    a tuple(callable, failure_type), or a list of several such elements. Nested lists are supported and indicate an
    implicit `and_` (such as the main list). Tuples indicate an implicit `_failure_raiser`.
    [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of callables, they will
    be transformed to functions automatically.
    :param error_type: a subclass of ValidationError to raise in case of validation failure. By default a
    ValidationError will be raised with the provided help_msg
    :param help_msg: an optional help message to be used in the raised error in case of validation failure.
    :param none_policy: describes how None values should be handled. See `NoneArgPolicy` for the various possibilities.
    Default is `NoneArgPolicy.ACCEPT_IF_OPTIONAl_ELSE_REJECT`.
    :param kw_context_args: optional contextual information to store in the exception, and that may be also used
    to format the help message
    :return: the decorated function, that will perform input validation (using `_assert_input_is_valid`) before
    executing the function's code everytime it is executed.
    """

    none_policy = none_policy or NoneArgPolicy.SKIP_IF_NONABLE_ELSE_VALIDATE

    # retrieve target function signature
    func_sig = signature(func)

    # create the new validator
    new_validator = _create_function_validator(func, func_sig, arg_name, *validation_func,
                                               none_policy=none_policy, error_type=error_type,
                                               help_msg=help_msg, **kw_context_args)

    # decorate or update decorator with this new validator
    return decorate_with_validators(func, **{arg_name: new_validator}, func_signature=func_sig)


def decorate_with_validators(func, func_signature: Signature = None, **validators: Validator):
    """
    Utility method to decorate the provided function with the provided input and output Validator objects. Since this
    method takes Validator objects as argument, it is for advanced users.

    :param func: the function to decorate. It might already be decorated, this method will check it and wont create
    another wrapper in this case, simply adding the validators to the existing wrapper
    :param func_signature: the function's signature if it is already known (internal calls), otherwise it will be found
    again by inspection
    :param validators: a dictionary of arg_name (or _out_) => Validator or list of Validator
    :return:
    """
    # first turn the dictionary values into lists only
    for arg_name, validator in validators.items():
        if not isinstance(validator, list):
            validators[arg_name] = [validator]

    if hasattr(func, '__wrapped__') and hasattr(func.__wrapped__, '__validators__'):
        # ---- This function is already wrapped by our validation wrapper ----

        # Update the dictionary of validators with the new validator(s)
        for arg_name, validator in validators.items():
            for v in validator:
                if arg_name in func.__wrapped__.__validators__:
                    func.__wrapped__.__validators__[arg_name].append(v)
                else:
                    func.__wrapped__.__validators__[arg_name] = [v]

        # return the function, no need to wrap it further (it is already wrapped)
        return func

    else:
        # ---- This function is not yet wrapped by our validator. ----

        # Store the dictionary of validators as an attribute of the function
        if hasattr(func, '__validators__'):
            raise ValueError('Function ' + str(func) + ' already has a defined __validators__ attribute, valid8 '
                             'decorators can not be applied on it')
        else:
            func.__validators__ = validators

        # either reuse or recompute function signature
        func_signature = func_signature or signature(func)

        # we used @functools.wraps(), but we now use 'decorate()' to have a wrapper that has the same signature
        def validating_wrapper(f, *args, **kwargs):
            """ This is the wrapper that will be called everytime the function is called """

            # (a) Perform input validation by applying `_assert_input_is_valid` on all received arguments
            apply_on_each_func_args_sig(f, args, kwargs, func_signature,
                                        func_to_apply=_assert_input_is_valid,
                                        func_to_apply_params_dict=f.__validators__)

            # (b) execute the function as usual
            res = f(*args, **kwargs)

            # (c) validate output if needed
            if _OUT_KEY in f.__validators__:
                for validator in f.__validators__[_OUT_KEY]:
                    validator.assert_valid(res)

            return res

        decorated_function = decorate(func, validating_wrapper)
        return decorated_function


def _assert_input_is_valid(input_value: Any, validators: List[InputValidator], validated_func: Callable,
                           input_name: str):
    """
    Called by the `validating_wrapper` in the first step (a) `apply_on_each_func_args` for each function input before
    executing the function. It simply delegates to the validator. The signature of this function is hardcoded to
    correspond to `apply_on_each_func_args`'s behaviour and should therefore not be changed.

    :param input_value: the value to validate
    :param validator: the Validator object that will be applied on input_value_to_validate
    :param validated_func: the function for which this validation is performed. This is not used since the Validator
    knows it already, but we should not change the signature here.
    :param input_name: the name of the function input that is being validated
    :return: Nothing
    """
    for validator in validators:
        validator.assert_valid(input_name, input_value)
