#!/usr/bin/env python

from __future__ import print_function

import json
import os
import sys
from cmd import Cmd

import click
from requests import ConnectionError

from stackdio.cli.mixins import blueprints, bootstrap, formulas, stacks
from stackdio.client import StackdioClient
from stackdio.client.version import __version__


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

HIST_FILE = os.path.join(os.path.expanduser('~'), '.stackdio-cli', 'history')


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-v', '--version')
@click.pass_context
def stackdio(ctx):
    client = StackdioClient()
    if ctx.invoked_subcommand not in ('configure', None) and not client.usable():
        raise click.UsageError('It looks like you haven\'t used this CLI before.  Please run '
                               '`stackdio-cli configure`')

    # Put the client in the obj
    ctx.obj['client'] = client


@stackdio.command()
@click.pass_obj
def configure(obj):
    client = obj['client']
    print('configuring')


@stackdio.command('server-version')
@click.pass_obj
def server_version(obj):
    client = obj['client']
    click.echo('stackdio-server, version {0}'.format(client.get_version()))


# Add all our other commands
stackdio.add_command(blueprints.blueprints)
stackdio.add_command(stacks.stacks)


class StackdioShell(Cmd, bootstrap.BootstrapMixin, stacks.StackMixin,
                    formulas.FormulaMixin):

    CFG_DIR = os.path.expanduser("~/.stackdio-cli/")
    CFG_FILE = os.path.join(CFG_DIR, "config.json")
    BOOTSTRAP_FILE = os.path.join(CFG_DIR, "bootstrap.yaml")
    KEYRING_SERVICE = "stackdio_cli"
    PROMPT = "\n{username} @ {url}\n> "
    HELP_CMDS = [
        "account_summary",
        "stacks", "blueprints", "formulas",
        "initial_setup", "bootstrap",
        "help", "exit", "quit",
    ]

    intro = """
######################################################################
                      s  t  a  c  k  d  .  i  o
######################################################################
"""

    def __init__(self):
        mixins.bootstrap.BootstrapMixin.__init__(self)
        self._load_config()
        if 'url' in self.config and self.config['url']:
            self._init_stacks()
        self._validate_auth()

    def _load_config(self):
        """Attempt to load config file, otherwise fallback to DEFAULT_CONFIG"""

        try:
            self.config = json.loads(open(self.CFG_FILE).read())
            self.config['blueprint_dir'] = os.path.expanduser(self.config.get('blueprint_dir', ''))

        except ValueError:
            print(self.colorize(
                "What happened?! The config file is not valid JSON. A "
                "re-install is likely the easiest fix.", "red"))
            raise
        except IOError:
            self.config = {
                'url': None,
                'username': None,
            }
            print(self.colorize(
                "It seems like this is your first time using the CLI.  Please run "
                "'initial_setup' to configure.", "green"))
            # print(self.colorize(
            #     "What happened?! Unable to find a config file. A re-install "
            #     "is likely the easiest fix.", "red"))
            # raise

        self.has_public_key = None

    def _validate_auth(self):
        """Verify that we can connect successfully to the api"""

        # If there is no config, just force the user to go through initial setup
        if self.config['url'] is None:
            return

        try:
            self.stacks.get_root()
            status_code = 200
            self.validated = (200 <= status_code <= 299)
        except ConnectionError:
            print(self.colorize(
                "Unable to connect to {0}".format(self.config["url"]),
                "red"))
            raise

        if self.validated:
            print(self.colorize(
                "Config loaded and validated", "blue"))
            self.has_public_key = self.stacks.get_public_key()
        else:
            print(self.colorize(
                "ERROR: Unable to validate config", "red"))
            self.has_public_key = None

    def _setprompt(self):

        Cmd.prompt = self.colorize(
            self.PROMPT.format(**self.config),
            "blue")

        if not self.validated and self.config['url'] is not None:
            print(self.colorize("""
##
## Unable to validate connection - one of several possibilities exist:
## If this is the first time you've fired this up, you need to run
## 'initial_setup' to configure your account details.  If you've already
## done that, there could be a network connection issue anywhere between
## your computer and your stackd.io instance,
## or your password may be incorrect, or ... etc.
##
                """,
                                "green"))

        if self.validated and not self.has_public_key:
            print(self.colorize(
                "## Your account is missing the public key, run 'bootstrap' to fix",
                "red"))

    def do_account_summary(self, args=None):
        """Get a summary of your account."""
        sys.stdout.write("Polling {0} ... ".format(self.config["url"]))
        sys.stdout.flush()

        public_key = self.stacks.get_public_key()
        formulas = self.stacks.list_formulas()
        blueprints = self.stacks.list_blueprints()
        stacks = self.stacks.list_stacks()

        sys.stdout.write("done\n")

        print("## Username: {0}".format(self.config["username"]))
        print("## Public Key:\n{0}".format(public_key))

        self._print_summary("Formula", formulas)
        self._print_summary("Blueprint", blueprints)
        self._print_summary("Stack", stacks)


def main():
    # Just run our CLI tool
    stackdio(obj={})


if __name__ == '__main__':
    main()
