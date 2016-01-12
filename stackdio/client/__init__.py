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

from .account import AccountMixin
from .blueprint import BlueprintMixin
from .config import StackdioConfig
from .exceptions import (
    BlueprintException,
    StackException,
    IncompatibleVersionException,
    MissingUrlException
)
from .formula import FormulaMixin
from .http import HttpMixin, get, post, patch
from .image import ImageMixin
from .region import RegionMixin
from .settings import SettingsMixin
from .stack import StackMixin
from .version import _parse_version_string

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class StackdioClient(BlueprintMixin, FormulaMixin, AccountMixin, ImageMixin,
                     RegionMixin, StackMixin, SettingsMixin, HttpMixin):

    def __init__(self, url=None, username=None, password=None, verify=True, cfg_file=None):
        self.config = StackdioConfig(cfg_file)

        self.url = None
        self.username = None
        self.password = None
        self.verify = None

        if self.config.usable_config:
            # Grab stuff from the config
            self.url = self.config.get('url')
            self.username = self.config.get('username')
            self.password = self.config.get_password()
            self.verify = self.config.get('verify', True)

        if url is not None:
            self.url = url

        if username is not None and password is not None:
            self.username = username
            self.password = password

        if verify is not None:
            self.verify = verify

        super(StackdioClient, self).__init__(url=self.url,
                                             auth=(self.username, self.password),
                                             verify=self.verify)

        if self.usable():
            try:
                _, self.version = _parse_version_string(self.get_version(raise_for_status=False))
            except MissingUrlException:
                self.version = None

            if self.version and (self.version[0] != 0 or self.version[1] != 7):
                raise IncompatibleVersionException('Server version {0}.{1}.{2} not '
                                                   'supported.'.format(**self.version))

    def usable(self):
        return self.url and self.username and self.password

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
    def create_security_group(self, name, description, cloud_account, group_id, is_default=True):

        return {
            'name': name,
            'description': description,
            'cloud_account': cloud_account,
            'group_id': group_id,
            'is_default': is_default
        }
