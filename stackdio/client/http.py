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

import json
import logging
from functools import update_wrapper
from inspect import getcallargs

import requests

from .exceptions import MissingUrlException

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

HTTP_INSECURE_MESSAGE = '\n'.join([
    "You have chosen not to verify ssl connections.",
    "This is insecure, but it's your choice.",
    "This has been your single warning."
])


class HttpMixin(object):
    """Add HTTP request features to an object"""

    HEADERS = {
        'json': {'content-type': 'application/json'},
        'xml': {'content-type': 'application/xml'},
    }

    def __init__(self):
        super(HttpMixin, self).__init__()
        self._http_log = logger

        if not self.verify:
            if self._http_log.handlers:
                self._http_log.warn(HTTP_INSECURE_MESSAGE)
            else:
                print(HTTP_INSECURE_MESSAGE)

            from requests.packages.urllib3 import disable_warnings
            disable_warnings()

    @property
    def url(self):
        raise NotImplementedError()

    @property
    def username(self):
        raise NotImplementedError()

    @property
    def password(self):
        raise NotImplementedError()

    @property
    def verify(self):
        raise NotImplementedError()

    def usable(self):
        raise NotImplementedError()


def default_response(obj, response):
    return response


def request(path, method, paginate=False, jsonify=True, **req_kwargs):

    # Define a class here that uses the path / method we want.  We need it inside this function
    # so we have access to the path / method.
    class Request(object):
        def __init__(self, dfunc=None, rfunc=None, quiet=False):
            super(Request, self).__init__()

            if dfunc:
                update_wrapper(self, dfunc)

            self.obj = None

            self.data_func = dfunc
            self.response_func = rfunc

            if self.response_func is None:
                self.response_func = default_response

            self.quiet = quiet

            self.headers = req_kwargs.get('headers', HttpMixin.HEADERS['json'])

            self._http_log = logging.getLogger(__name__)

        def data(self, dfunc):
            return type(self)(dfunc, self.response_func, self.quiet)

        def response(self, rfunc):
            return type(self)(self.data_func, rfunc, self.quiet)

        def __repr__(self):
            if self.obj:
                return ('<bound method HTTP {0} request for '
                        '\'/api/{1}\' on {2}>'.format(method, path, repr(self.obj)))
            else:
                return super(Request, self).__repr__()

        # We need this so we can save the client object as an attribute, and then it can be used
        # in __call__
        def __get__(self, obj, objtype=None):
            if objtype:
                assert issubclass(objtype, HttpMixin)
            assert isinstance(obj, HttpMixin)

            self.obj = obj
            return self

        # Here's how the request actually happens
        def __call__(self, *args, **kwargs):
            assert isinstance(self.obj, HttpMixin)

            if not self.obj.usable():
                raise MissingUrlException('No url is set.  Please run `configure`.')

            none_on_404 = kwargs.pop('none_on_404', False)
            raise_for_status = kwargs.pop('raise_for_status', True)

            # Get what locals() would return directly after calling
            # 'func' with the given args and kwargs
            future_locals = getcallargs(self.data_func, *((self.obj,) + args), **kwargs)

            # Build the variable we'll inject
            url = '{url}{path}'.format(
                url=self.obj.url,
                path=path.format(**future_locals)
            )

            if not self.quiet:
                self._http_log.info("%s: %s", method, url)

            data = None
            if self.data_func:
                data = json.dumps(self.data_func(self.obj, *args, **kwargs))

            result = requests.request(method,
                                      url,
                                      data=data,
                                      auth=(self.obj.username, self.obj.password),
                                      headers=self.headers,
                                      params=kwargs,
                                      verify=self.obj.verify)

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

            if jsonify:
                response = result.json()
            else:
                response = result.text

            if method == 'GET' and paginate and jsonify:
                res = response['results']

                next_url = response.get('next')

                while next_url:
                    next_page = requests.request(method,
                                                 next_url,
                                                 data=data,
                                                 auth=(self.obj.username, self.obj.password),
                                                 headers=self.headers,
                                                 params=kwargs,
                                                 verify=self.obj.verify).json()
                    res.extend(next_page['results'])
                    next_url = next_page.get('next')

                response = res

            # now process the result
            return self.response_func(self.obj, response)

    return Request


# Define the decorators for all the methods
def get(path, paginate=False, jsonify=True):
    return request(path, 'GET', paginate=paginate, jsonify=jsonify)


def head(path):
    return request(path, 'HEAD')


def options(path):
    return request(path, 'OPTIONS')


def post(path):
    return request(path, 'POST')


def put(path):
    return request(path, 'PUT')


def patch(path):
    return request(path, 'PATCH')


def delete(path):
    return request(path, 'DELETE')
