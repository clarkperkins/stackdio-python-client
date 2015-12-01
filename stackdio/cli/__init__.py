#!/usr/bin/env python

from __future__ import print_function

import argparse
import json
import os
import sys

import keyring
from cmd2 import Cmd
from requests import ConnectionError

from stackdio.cli import mixins
from stackdio.client import StackdIO


class StackdioShell(Cmd, mixins.bootstrap.BootstrapMixin, mixins.stacks.StackMixin,
                    mixins.formulas.FormulaMixin, mixins.blueprints.BlueprintMixin):

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

    Cmd.intro = """
######################################################################
                      s  t  a  c  k  d  .  i  o
######################################################################
"""

    def __init__(self):
        Cmd.__init__(self)
        mixins.bootstrap.BootstrapMixin.__init__(self)
        self._load_config()
        if 'url' in self.config and self.config['url']:
            self._init_stacks()
        self._validate_auth()

    def preloop(self):
        self._setprompt()

    def precmd(self, line):
        self._setprompt()
        return line

    def postloop(self):
        print("\nGoodbye!")

    def get_names(self):
        if self.validated:
            return ["do_%s" % c for c in self.HELP_CMDS]
        else:
            return ["do_initial_setup", "do_help"]

    def _init_stacks(self):
        """Instantiate a StackdIO object"""
        self.stacks = StackdIO(
            base_url=self.config["url"],
            auth=(
                self.config["username"],
                keyring.get_password(self.KEYRING_SERVICE, self.config.get("username") or "")
            ),
            verify=self.config.get('verify', True)
        )

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

    def _print_summary(self, title, components):
        num_components = len(components)
        print("## {0} {1}{2}".format(
            num_components,
            title,
            "s" if num_components == 0 or num_components > 1 else ""))

        for item in components:
            print("- Title: {0}\n  Description: {1}".format(
                item.get("title"), item.get("description")))

            if "status_detail" in item:
                print("  Status Detail: {0}\n".format(
                    item.get("status_detail")))
            else:
                print("")

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
    parser = argparse.ArgumentParser(
        description="Invoke the stackdio cli")
    parser.add_argument("--debug", action="store_true", help="Enable debugging output")
    args = parser.parse_args()

    # an ugly hack to work around the fact that cmd2 is using optparse to parse
    # arguments for the commands; not sure what the "right" fix is, but as long
    # as we assume that we don't want any of our arguments to get passed into
    # the cmdloop this seems ok
    sys.argv = sys.argv[0:1]

    shell = StackdioShell()
    if args.debug:
        shell.debug = True
    shell.cmdloop()


if __name__ == '__main__':
    main()
