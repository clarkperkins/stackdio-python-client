import logging
import requests

class NoAdminException(Exception):
    pass


def use_admin_auth(func):
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


class HttpMixin(object):
    """Add HTTP request features to an object"""

    HEADERS = {
        'json': {"content-type": "application/json"},
#        'xml': {"content-type": "application/xml"}
    }

    def __init__(self, auth=None, verify=True):
        self._http_options = {}
        self._http_options['auth'] = auth
        self._http_options['verify'] = verify
        self._http_log = logging.getLogger(__name__)


    def _request(self, verb, url, quiet=False, none_on_404=False, *args, **kwargs):
        """Generic request method"""
        if not quiet:
            self._http_log().info("{0}: {1}".format(verb, url))

        headers = kwargs.get('headers', HttpMixin.HEADERS['json'])
        result = requests.request(verb, url,
                                  auth=self._http_options['auth'],
                                  headers=headers,
                                  verify=self._http_options['verify'],
                                  *args, **kwargs)
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
