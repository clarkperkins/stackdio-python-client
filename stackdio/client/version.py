# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import datetime
import operator
import os
import re
import subprocess
import warnings
from functools import wraps

# for setup.py
try:
    from .exceptions import IncompatibleVersionException, InvalidVersionStringException
except Exception:
    pass

VERSION = (0, 7, 1, 'dev', 0)


def get_version(version):
    """
    Returns a PEP 440-compliant version number from VERSION.

    Created by modifying django.utils.version.get_version
    """

    # Now build the two parts of the version number:
    # major = X.Y[.Z]
    # sub = .devN - for development releases
    #     | {a|b|rc}N - for alpha, beta and rc releases
    #     | .postN - for post-release releases

    assert len(version) == 5

    version_parts = version[:3]

    # Build the first part of the version
    major = '.'.join(str(x) for x in version_parts)

    # Just return it if this is a final release version
    if version[3] == 'final':
        return major

    # Add the rest
    sub = ''.join(str(x) for x in version[3:5])

    if version[3] == 'dev':
        # Override the sub part.  Add in a timestamp
        timestamp = get_git_changeset()
        sub = 'dev%s' % (timestamp if timestamp else '')
        return '%s.%s' % (major, sub)
    if version[3] == 'post':
        # We need a dot for post
        return '%s.%s' % (major, sub)
    elif version[3] in ('a', 'b', 'rc'):
        # No dot for these
        return '%s%s' % (major, sub)
    else:
        raise ValueError('Invalid version: %s' % str(version))


# Borrowed directly from django
def get_git_changeset():
    """Returns a numeric identifier of the latest git changeset.

    The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
    This value isn't guaranteed to be unique, but collisions are very unlikely,
    so it's sufficient for generating the development version numbers.
    """
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    git_log = subprocess.Popen('git log --pretty=format:%ct --quiet -1 HEAD',
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               shell=True, cwd=repo_dir, universal_newlines=True)
    timestamp = git_log.communicate()[0]
    try:
        timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
        return timestamp.strftime('%Y%m%d%H%M%S')
    except ValueError:
        return None


__version__ = get_version(VERSION)


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
    if version_string[-1] == '.':
        version_string = version_string[:-1]
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
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)

    return wrapper
