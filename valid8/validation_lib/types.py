from valid8.base import Failure


class HasWrongType(Failure):
    """ Custom Failure raised by instance_of """
    help_msg = 'Value should be an instance of {ref_type}'


def instance_of(ref_type):
    """ 'instance of' validation_function generator. Returns a validation function to check that
    `is_instance(x, ref_type)`. """
    def instance_of_ref(x):
        if isinstance(x, ref_type):
            return True
        else:
            raise HasWrongType(wrong_value=x, ref_type=ref_type)

    instance_of_ref.__name__ = 'instance_of_{}'.format(ref_type)
    return instance_of_ref


class IsWrongType(Failure):
    """ Custom Failure raised by subclass_of """
    help_msg = 'Value should be a type that is a subclass of {ref_type}'


def subclass_of(ref_type):
    """ 'subclass of' validation_function generator. Returns a validation function to check that
    `is_subclass(x, ref_type)`. """

    def subclass_of_ref(x):
        if type(x) is type and issubclass(x, ref_type):
            return True
        else:
            raise IsWrongType(wrong_value=x, ref_type=ref_type)

    subclass_of_ref.__name__ = 'subclass_of_{}'.format(ref_type)
    return subclass_of_ref