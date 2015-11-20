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

import logging

from .http import get, post, patch
from .exceptions import BlueprintException, StackException, IncompatibleVersionException

from .blueprint import BlueprintMixin
from .formula import FormulaMixin
from .account import AccountMixin
from .image import ImageMixin
from .region import RegionMixin
from .settings import SettingsMixin
from .stack import StackMixin

from .version import _parse_version_string

logger = logging.getLogger(__name__)


class StackdIO(BlueprintMixin, FormulaMixin, AccountMixin,
               ImageMixin, RegionMixin, StackMixin, SettingsMixin):

    def __init__(self, protocol="https", host="localhost", port=443,
                 base_url=None, auth=None, auth_admin=None,
                 verify=True):
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

        if self.version[0] != 0 or self.version[1] != 7:
            raise IncompatibleVersionException('Server version {0}.{1}.{2} not '
                                               'supported.'.format(**self.version))

    @get('')
    def get_root(self):
        pass

    @get('version/')
    def get_version(self):
        pass

    @get_version.response
    def get_version(self, resp):
        return resp['version']

    @post('cloud/security_groups/')
    def create_security_group(self, name, description, cloud_provider, is_default=True):
        """Create a security group"""

        return {
            "name": name,
            "description": description,
            "cloud_provider": cloud_provider,
            "is_default": is_default
        }
