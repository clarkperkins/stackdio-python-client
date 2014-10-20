import json
import logging

from .http import use_admin_auth, endpoint
from .exceptions import BlueprintException, StackException

from .blueprint import BlueprintMixin
from .formula import FormulaMixin
from .profile import ProfileMixin
from .provider import ProviderMixin
from .region import RegionMixin
from .settings import SettingsMixin
from .stack import StackMixin

from .version import _parse_version_string

logger = logging.getLogger(__name__)


class StackdIO(BlueprintMixin, FormulaMixin, ProfileMixin,
               ProviderMixin, RegionMixin, StackMixin, SettingsMixin):

    def __init__(self, protocol="https", host="localhost", port=443,
                 base_url=None, auth=None, auth_admin=None,
                 verify=False):
        """auth_admin is optional, only needed for creating provider, profile,
        and base security groups"""

        super(StackdIO, self).__init__(auth=auth, verify=verify)
        if base_url:
            self.url = base_url if base_url.endswith('/') else "%s/" % base_url
        else:
            self.url = "{protocol}://{host}:{port}/api/".format(
                protocol=protocol,
                host=host,
                port=port)

        self.auth = auth
        self.auth_admin = auth_admin

        _, self.version = _parse_version_string(self.get_version())

    @endpoint("")
    def get_root(self):
        """Get the api root"""
        return self._get(endpoint, jsonify=True)

    @endpoint("version/")
    def get_version(self):
        return self._get(endpoint, jsonify=True)['version']

    @endpoint("blueprints/{blueprint_id}/")
    def delete_blueprint(self, blueprint_id):
        result = self._delete(endpoint, jsonify=True)
        if result is None:
            raise BlueprintException("Blueprint %s not found" % blueprint_id)
        else:
            return result

    @use_admin_auth
    @endpoint("security_groups/")
    def create_security_group(self, name, description, cloud_provider, is_default=True):
        """Create a security group"""

        data = {
            "name": name,
            "description": description,
            "cloud_provider": cloud_provider,
            "is_default": is_default
        }
        return self._post(endpoint, data=json.dumps(data), jsonify=True)

    @endpoint("settings/")
    def get_public_key(self):
        """Get the public key for the logged in uesr"""
        return self._get(endpoint, jsonify=True)['public_key']

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

    @endpoint("instance_sizes/")
    def get_instance_id(self, instance_id, provider_type="ec2"):
        """Get the id for an instance_id. The instance_id parameter is the
        provider name (e.g. m1.large). The id returned is the stackd.io id
        for use in API calls (e.g. 1)."""

        result = self._get(endpoint, jsonify=True)
        for instance in result['results']:
            if instance.get("instance_id") == instance_id and \
               instance.get("provider_type") == provider_type:
                return instance.get("id")

        raise StackException("Instance type %s from provider %s not found" %
                             (instance_id, provider_type))
