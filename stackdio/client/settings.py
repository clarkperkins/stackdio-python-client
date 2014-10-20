import json
import os

from .http import HttpMixin, endpoint


class SettingsMixin(HttpMixin):

    @endpoint("settings/")
    def set_public_key(self, public_key):
        """Upload a public key for our user. public_key can be the actual key, a
        file handle, or a path to a key file"""

        if isinstance(public_key, file):
            public_key = public_key.read()

        elif isinstance(public_key, str) and os.path.exists(public_key):
            public_key = open(public_key, "r").read()

        data = {
            "public_key": public_key
        }
        return self._put(endpoint, data=json.dumps(data), jsonify=True)
