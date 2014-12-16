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

from __future__ import print_function

import logging
import requests

from functools import wraps
from inspect import getcallargs

from .exceptions import NoAdminException

logger = logging.getLogger(__name__)

HTTP_INSECURE_MESSAGE = "\n".join([
    "You have chosen not to verify ssl connections.",
    "This is insecure, but it's your choice.",
    "This has been your single warning."])


def use_admin_auth(func):

    @wraps(func)
    def wrapper(obj, *args, **kwargs):
        # Save and set the auth to use the admin auth
        auth = obj._http_options['auth']
        try:
            obj._http_options['auth'] = obj._http_options['admin']
        except KeyError:
            raise NoAdminException("No admin credentials were specified")

        # Call the original function
        output = func(*args, **kwargs)

        # Set the auth back to the original
        obj._http_options['auth'] = auth
        return output
    return wrapper


def endpoint(path):
    """Takes a path extension and appends to the known API base url.
    The result of this is then added to the decorated functions global
    scope as a variable named 'endpoint"""
    def decorator(func):
        @wraps(func)
        def wrapper(obj, *args, **kwargs):

            # Get what locals() would return directly after calling
            # 'func' with the given args and kwargs
            future_locals = getcallargs(func, *((obj,) + args), **kwargs)

            # Build the variable we'll inject
            url = "{url}{path}".format(
                url=obj.url,
                path=path.format(**future_locals))

            # Grab the global context for the passed function
            g = func.__globals__

            # Create a unique default object so we can accurately determine
            # if we replaced a value
            sentinel = object()
            oldvalue = g.get('endpoint', sentinel)

            # Inject our variable into the global scope
            g['endpoint'] = url

            # Logging and function call
            if oldvalue:
                logger.debug("Value %s for 'endpoint' replaced in global scope "
                             "for function %s" % (oldvalue, func.__name__))
            logger.debug("%s.__globals__['endpoint'] = %s" % (func.__name__, url))

            result = func(obj, *args, **kwargs)

            # Replace the previous value, if it existed
            if oldvalue is not sentinel:
                g['endpoint'] = oldvalue

            return result
        return wrapper
    return decorator


class HttpMixin(object):
    """Add HTTP request features to an object"""

    HEADERS = {
        'json': {"content-type": "application/json"},
        'xml': {"content-type": "application/xml"}
    }

    def __init__(self, auth=None, verify=True):
        self._http_options = {
            'auth': auth,
            'verify': verify,
        }
        self._http_log = logging.getLogger(__name__)

        if not verify:
            if self._http_log.handlers:
                self._http_log.warn(HTTP_INSECURE_MESSAGE)
            else:
                print(HTTP_INSECURE_MESSAGE)

            from requests.packages.urllib3 import disable_warnings
            disable_warnings()



    def _request(self, verb, url, quiet=False,
                 none_on_404=False, jsonify=False, raise_for_status=True,
                 *args, **kwargs):
        """Generic request method"""
        if not quiet:
            self._http_log.info("{0}: {1}".format(verb, url))

        headers = kwargs.get('headers', HttpMixin.HEADERS['json'])

        result = requests.request(verb, url,
                                  auth=self._http_options['auth'],
                                  headers=headers,
                                  verify=self._http_options['verify'],
                                  *args, **kwargs)

        # Handle special conditions
        if none_on_404 and result.status_code == 404:
            return None

        elif result.status_code == 204:
            return None

        elif raise_for_status:
            try:
                result.raise_for_status()
            except Exception:
                logger.error(result.text)
                raise

        # return
        if jsonify:
            return result.json()
        else:
            return result

    def _head(self, url, *args, **kwargs):
        return self._request("HEAD", url, *args, **kwargs)

    def _get(self, url, *args, **kwargs):
        return self._request("GET", url, *args, **kwargs)

    def _delete(self, url, *args, **kwargs):
        return self._request("DELETE", url, *args, **kwargs)

    def _post(self, url, data=None, *args, **kwargs):
        return self._request("POST", url, data=data, *args, **kwargs)

    def _put(self, url, data=None, *args, **kwargs):
        return self._request("PUT", url, data=data, *args, **kwargs)

    def _patch(self, url, data=None, *args, **kwargs):
        return self._request("PATCH", url, data=data, *args, **kwargs)
