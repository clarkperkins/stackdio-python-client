import logging
import requests

from functools import wraps
from inspect import getcallargs
from simplejson import JSONDecodeError

from .exceptions import NoAdminException, StackException

logger = logging.getLogger(__name__)


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


def jsonify_result(func):

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)

            logger.info("{funcname} result:\n"
                        "{text}".format(funcname=func.__name__,
                                        text=result.text))

            return result.json()['results']

        except JSONDecodeError, e:
            raise StackException("Unable to decode json;\n"
                                 "Request results: %s\n"
                                 "Exception: %s",
                                 result.text, e)
    return wrapper




def endpoint(path):
    """Takes a path extension and appends to the known API base url.
    The result of this is then added to the decorated functions global
    scope as a variable named 'endpoint"""
    def decorator(func):
        @wraps(func)
        def wrapper(obj, *args, **kwargs):

            future_locals = getcallargs(func, *((obj,) + args), **kwargs)
            url = "{url}{path}".format(
                url=obj.url,
                path=path.format(**future_locals))

            g = func.__globals__
            oldvalue = g.get('endpoint')
            g['endpoint'] = url

            if oldvalue:
                logger.warn("Value %s for 'endpoint' replaced in global scope "
                            "for function %s" % (oldvalue, func.__name__))
            logger.debug("%s.__globals__['endpoint'] = %s" % (func.__name__, url))

            return func(obj, *args, **kwargs)
        return wrapper
    return decorator


class HttpMixin(object):
    """Add HTTP request features to an object"""

    HEADERS = {
        'json': {"content-type": "application/json"},
        #'xml': {"content-type": "application/xml"}
    }

    def __init__(self, auth=None, verify=True):
        self._http_options = {}
        self._http_options['auth'] = auth
        self._http_options['verify'] = verify
        self._http_log = logging.getLogger(__name__)


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

        elif raise_for_status:
            result.raise_for_status()

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
