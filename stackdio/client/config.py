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
import keyring
import requests
from requests.exceptions import ConnectionError, MissingSchema

from stackdio.client.compat import ConfigParser, NoOptionError


CFG_DIR = os.path.join(os.path.expanduser('~'), '.stackdio')
CFG_FILE = os.path.join(CFG_DIR, 'client.cfg')


class UserPath(click.Path):

    def convert(self, value, param, ctx):
        return super(UserPath, self).convert(os.path.expanduser(value), param, ctx)


class StackdioConfig(object):
    """
    A wrapper around python's ConfigParser class
    """

    KEYRING_SERVICE = 'stackdio_cli'

    BOOL_MAP = {
        str(True): True,
        str(False): False,
    }

    def __init__(self, config_file=None, section='stackdio'):
        super(StackdioConfig, self).__init__()

        self.section = section

        self._cfg_file = os.path.abspath(config_file or CFG_FILE)

        self._config = ConfigParser()

        self.usable_file = os.path.isfile(self._cfg_file)

        if self.usable_file:
            self._config.read(self._cfg_file)

        self.usable_section = self._config.has_section(self.section)
        self.usable_config = self.usable_file and self.usable_section

        if not self.usable_section:
            self._config.add_section(section)

    def save(self):
        full_path = os.path.dirname(self._cfg_file)

        if not os.path.isdir(full_path):
            os.makedirs(full_path)

        with open(self._cfg_file, 'w') as f:
            self._config.write(f)

    def get_password(self, username=None):
        username = username or self.get('username')

        if username is not None:
            return keyring.get_password(self.KEYRING_SERVICE, username)
        else:
            return None

    def set_password(self, new_password):
        username = self.get('username')

        if username is None:
            raise KeyError('Not username provided')

        keyring.set_password(self.KEYRING_SERVICE, username, new_password)

    def __contains__(self, item):
        try:
            self._config.get(self.section, item)
            return True
        except NoOptionError:
            return False

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
        self.get_username()
        self.get_blueprint_dir()

        # Save when we're done
        self.save()

    def _test_url(self, url):
        try:
            r = requests.get(url, verify=self.get('verify', True))
            return (200 <= r.status_code < 300) or r.status_code == 403
        except ConnectionError:
            return False
        except MissingSchema:
            click.echo('You might have forgotten http:// or https://')
            return False

    def _test_credentials(self, username, password):
        try:
            r = requests.get(self['url'],
                             verify=self.get('verify', True),
                             auth=(username, password))
            return 200 <= r.status_code < 300
        except (ConnectionError, MissingSchema):
            click.echo('There is something wrong with your URL.')
            return False

    def get_url(self):
        if self.get('url') is not None:
            if click.confirm('Keep existing url ({0})?'.format(self['url']), default=True):
                return

        self['verify'] = not click.confirm('Does your stackd.io server have a self-signed '
                                           'SSL certificate?')

        new_url = None

        while new_url is None:
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
                new_url = url
            else:
                click.echo('There was an error while attempting to contact that server.  '
                           'Try again.')

        self['url'] = new_url

    def get_username(self):
        valid_creds = False

        while not valid_creds:
            keep_username = False

            username = self.get('username')

            if username is not None:
                if click.confirm('Keep existing username ({0})?'.format(username), default=True):
                    keep_username = True

            if not keep_username:
                username = click.prompt('What is your stackd.io username', prompt_suffix='? ')

            password = self.get_password(username)

            keep_password = False

            if password is not None:
                if click.confirm('Keep existing password for user {0}?'.format(username),
                                 default=True):
                    keep_password = True

            if not keep_password:
                password = click.prompt('What is the password for {0}'.format(username),
                                        prompt_suffix='? ', hide_input=True)

            if self._test_credentials(username, password):
                self['username'] = username
                self.set_password(password)
                valid_creds = True
            else:
                click.echo('Invalid credentials.  Please try again.')
                valid_creds = False

    def get_blueprint_dir(self):
        blueprints = self.get('blueprint_dir')

        if blueprints is not None:
            if click.confirm('Keep existing blueprints directory ({0})?'.format(blueprints),
                             default=True):
                return

        self['blueprint_dir'] = click.prompt('Where are your blueprints stored',
                                             prompt_suffix='? ',
                                             type=UserPath(exists=True, file_okay=False,
                                                           resolve_path=True))


# FOR BACKWARDS COMPATIBILITY!!! To be removed at some point.
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-o', '--old-file', default=os.path.expanduser('~/.stackdio-cli/config.json'),
              type=click.Path(exists=True), help='Path to the old JSON config file')
@click.option('-n', '--new-file', default=CFG_FILE, type=click.Path(),
              help='Path to the new cfg format file.  Must not already exist.')
def migrate_old_config(old_file, new_file):
    """
    Used to migrate an old JSON config file to a new one
    """
    if os.path.exists(new_file):
        raise click.UsageError('The new config file must not already exist')

    old_keys = ['username', 'url', 'verify', 'blueprint_dir']

    config = StackdioConfig(new_file)

    import json
    with open(old_file, 'r') as f:
        old_config = json.load(f)

        for key in old_keys:
            if key in old_config:
                config[key] = old_config[key]

    if 'url' not in config:
        config.get_url()

    if 'username' not in config or config.get_password() is None:
        config.get_username()

    if 'blueprint_dir' not in config:
        config.get_blueprint_dir()

    config.save()


def main():
    migrate_old_config()


if __name__ == '__main__':
    main()
