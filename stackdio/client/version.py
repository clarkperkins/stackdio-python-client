__version__ = "0.0.6.client.1"

from functools import wraps
import operator
import re
import warnings

from .exceptions import (IncompatibleVersionException,
                         InvalidVersionStringException)


def _unsupported_function(func, current_version, accepted_versions):
    raise IncompatibleVersionException("%s: %s is not one of %s" %
                                       (func.__name__,
                                        ".".join([str(v) for v in current_version]),
                                        list(accepted_versions)))


def _parse_version_string(version_string):
    original_version_string = version_string
    comparisons = {
        "=": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        ">": operator.gt,
        "<=": operator.le,
        ">=": operator.ge
    }

    # Determine the comparison function
    comp_string = "="
    if version_string[0] in ["<", ">", "=", "!"]:
        offset = 1
        if version_string[1] == "=":
            offset += 1

        comp_string = version_string[:offset]
        version_string = version_string[offset:]

    # Check if the version appears compatible
    try:
        int(version_string[0])
    except ValueError:
        raise InvalidVersionStringException(original_version_string)

    # String trailing info
    version_string = re.split("[a-zA-Z]", version_string)[0]
    version = version_string.split(".")

    # Pad length to 3
    version += [0] * (3 - len(version))

    # Convert to ints
    version = [int(num) for num in version]

    try:
        return comparisons[comp_string], tuple(version)
    except KeyError:
        raise InvalidVersionStringException(original_version_string)


def accepted_versions(*versions):
    def decorator(func):
        if not versions:
            return func

        parsed_versions = [_parse_version_string(version_string)
                           for version_string in versions]

        @wraps(func)
        def wrapper(obj, *args, **kwargs):
            for parsed_version in parsed_versions:
                comparison, version = parsed_version
                if comparison(obj.version, version):
                    return func(obj, *args, **kwargs)

            return _unsupported_function(func, obj.version, versions)
        return wrapper
    return decorator


def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.'''

    @wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)

    return wrapper
