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

import os

import click
import requests
from requests.exceptions import ConnectionError, MissingSchema

from stackdio.client.compat import ConfigParser, NoOptionError


CFG_DIR = os.path.join(os.path.expanduser('~'), '.stackdio')
CFG_FILE = os.path.join(CFG_DIR, 'client.cfg')


class StackdioConfig(object):
    """
    A wrapper around python's ConfigParser class
    """

    BOOL_MAP = {
        str(True): True,
        str(False): False,
    }

    def __init__(self, config_file=CFG_FILE, section='default'):
        super(StackdioConfig, self).__init__()

        self.section = section

        self._cfg_file = config_file

        self.usable_config = os.path.isfile(config_file)

        self._config = ConfigParser()

        if not self.usable_config:
            self._config.add_section(section)
        else:
            self._config.read(config_file)

            # Make the blueprint dir usable
            blueprint_dir = self.get('blueprint_dir')
            if blueprint_dir:
                new_blueprint_dir = os.path.expanduser(blueprint_dir)
                self._config.set(section, 'blueprint_dir', new_blueprint_dir)

    def save(self):
        with open(self._cfg_file, 'w') as f:
            self._config.write(f)

    def __getitem__(self, item):
        try:
            ret = self._config.get(self.section, item)
            if ret in self.BOOL_MAP:
                return self.BOOL_MAP[ret]
            else:
                return str(ret)
        except NoOptionError:
            raise KeyError(item)

    def __setitem__(self, key, value):
        if isinstance(value, bool):
            value = str(value)
        self._config.set(self.section, key, value)

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def items(self):
        return self._config.items(self.section)

    def prompt_for_config(self):
        self.get_url()

    def _test_url(self, url):
        try:
            r = requests.get(url, verify=self.get('verify', True))
            return (200 <= r.status_code < 300) or r.status_code == 403
        except ConnectionError:
            return False
        except MissingSchema:
            click.echo('You might have forgotten http:// or https://')
            return False

    def get_url(self):

        if self.get('url') is not None:
            val = click.prompt('Keep existing url', default='y', prompt_suffix=' (y|n)? ')
            if val not in ('N', 'n'):
                return

        val = click.prompt('Does your stackd.io server have a self-signed SSL certificate',
                           default='n', prompt_suffix=' (y|n)? ')

        if val in ('Y', 'y'):
            self['verify'] = False
        else:
            self['verify'] = True

        self['url'] = None

        while self['url'] is None:
            url = click.prompt('What is the URL of your stackd.io server', prompt_suffix='? ')
            if url.endswith('api'):
                url += '/'
            elif url.endswith('api/'):
                pass
            elif url.endswith('/'):
                url += 'api/'
            else:
                url += '/api/'
            if self._test_url(url):
                self['url'] = url
            else:
                click.echo('There was an error while attempting to contact that server.  '
                           'Try again.')
