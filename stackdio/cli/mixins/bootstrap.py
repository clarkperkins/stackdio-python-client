import getpass
import json
import os
import sys

import requests
from requests import ConnectionError
from requests.exceptions import MissingSchema
from cmd2 import Cmd
import keyring
import yaml

from stackdio.cli.polling import poll_and_wait, TimeoutException


class PublicKeyNotFound(Exception):
    pass


class BootstrapMixin(Cmd):

    def __init__(self):

        # quieting down pylint
        self.has_public_key = None
        self.validated = False
        self.stacks = None
        self.config = None
        self.bootstrap_data = None
    
    def do_initial_setup(self, args=None):
        """Perform setup for your stackd.io account"""

        print("Performing initial setup")
        special_config = raw_input("Do you have your own config.json file you would like to use (y/n)? ")

        config_from_file = special_config in ['Y', 'y']

        if config_from_file:
            # Prompt for the filename where the config is located
            config_file = raw_input("Where is the file located? ")

            # Load the config file
            if os.path.exists(config_file):
                config = json.load(open(config_file, "r"))
            elif os.path.exists(os.path.expanduser(config_file)):
                config = json.load(open(os.path.expanduser(config_file), "r"))
            else:
                print("Unable to find the file.")
                return

            # Put the config file contents into the config object
            for k, v in config.iteritems():
                self.config[k] = v

            # Validate the url, prompt for a new one if invalid
            if not self.config.has_key('url') or not self._test_url(self.config['url']):
                print("There seems to be an issue with the url you provided.")
                self.config['url'] = None
                self._get_url()

        else:
            # No config file, just prompt individually
            self._get_url()

        self._get_user_creds()
        self._init_stacks()
        self._validate_auth()
        if not self.validated:
            return

        if not config_from_file and 'profile' in self.config:
            keep_profile = raw_input("Would you like to keep your current default profile (y/n)? ")

            if keep_profile in ['N', 'n']:
                self._choose_profile()

        # Only prompt for default profile if it's not already there
        if not self.config.has_key('profile') \
                or 'provider' not in self.config \
                or 'provider_type' not in self.config:
            if 'profile' in self.config:
                print("Profile misconfiguration detected.")
            self._choose_profile()

        get_dir = not config_from_file

        if not config_from_file and 'blueprint_dir' in self.config:
            keep_dir = raw_input("Would you like to keep your current blueprint directory (y/n)? ")

            if keep_dir not in ['N', 'n']:
                get_dir = False

        if get_dir:
            new_dir = raw_input("Enter the path of your blueprint templates: ")
            self.config['blueprint_dir'] = new_dir

        self._save_config()
        self._setprompt()

        if self.validated:
            bootstrap = raw_input("Bootstrap your account now (y/n)? ")
            if bootstrap not in ["y", "Y"]:
                return
            self.do_bootstrap()

            print(self.colorize("""
## 
## Success!  You're ready to start using stackd.io.  Try running
## 'help' to see what all is available here.  You can also go to
## {0} to use the UI.
##
                """.format(
                    self.config["url"][0:self.config["url"].find("api/")]), 
                "green"))
            
        else:
            print(self.colorize(
                "Unable to bootstrap your account",
                "red"))
            return

    def do_bootstrap(self, args=None):
        """Bootstrap an account with predefined formulas and blueprints"""

        args = args or []

        if not self.validated:
            print(self.colorize(
                "You must run 'initial_setup' before you can bootstrap",
                "red"))
            return

        if not self.config.has_key('profile'):
            print(self.colorize("You must have a default profile in order to run bootstrap.  Run 'initial_setup'",
                                "red"))
            return
    
        print("Bootstrapping your account")

        custom_bootstrap = raw_input("Do you have a custom bootstrap yaml file (y/n)? ")

        if custom_bootstrap in ['Y', 'y']:
            custom_bootstrap_file = raw_input("Enter the name of the file: ")

            # Load the bootstrap file
            if os.path.exists(custom_bootstrap_file):
                self.BOOTSTRAP_FILE = custom_bootstrap_file
            elif os.path.exists(os.path.expanduser(custom_bootstrap_file)):
                self.BOOTSTRAP_FILE = os.path.expanduser(custom_bootstrap_file)
            else:
                print("Unable to find the file.")
                use_default = raw_input("Would you like to use the default bootstrap file instead (y/n)? ")
                if use_default not in ['Y', 'y']:
                    print("Aborting bootstrap")
                    return

        # Load the bootstrap data.  If the BOOTSTRAP_DATA property was not set just now, it will use the default
        self.bootstrap_data = yaml.safe_load(open(self.BOOTSTRAP_FILE).read())

        self._bootstrap_account()
        self._bootstrap_formulas()
        self._bootstrap_blueprints()

    def _test_url(self, url):
        try:
            r = requests.get(url, verify=self.config.get('verify', True))
            return (200 <= r.status_code < 300) or r.status_code == 403
        except ConnectionError:
            return False
        except MissingSchema:
            print("You might have forgotten http:// or https://")
            return False

    def _get_url(self):
        """Prompt user for url"""

        if self.config['url'] is not None:
            keep_url = raw_input("Keep existing url (y/n)? ")
            if keep_url not in ["n", "N"]:
                return

        verify = raw_input("Does your stackd.io server have a self-signed SSL certificate (y/n)? ")
        if verify in ('Y', 'y'):
            self.config['verify'] = False
        else:
            self.config['verify'] = True

        self.config['url'] = None

        while self.config['url'] is None:
            url = raw_input("What is the URL of your stackd.io server? ")
            if url.endswith('api'):
                url += '/'
            elif url.endswith('api/'):
                pass
            elif url.endswith('/'):
                url += 'api/'
            else:
                url += '/api/'
            if self._test_url(url):
                self.config['url'] = url
            else:
                print("There was an error while attempting to contact that server.  Try again.")

    def _get_user_creds(self):
        """Prompt user for credentials"""

        self.config["username"] = raw_input("What is your username? ")
        
        if keyring.get_password(self.KEYRING_SERVICE, self.config["username"]):
            print("Password already stored for {0}".format(self.config["username"]))
            keep_password = raw_input("Keep existing password (y/n)? ")
        else: 
            keep_password = "n"

        if keep_password in ["n", "N"]:
            password = getpass.getpass("What is your password? ")
            keyring.set_password(self.KEYRING_SERVICE,
                                 self.config["username"],
                                 password)

    def _choose_profile(self):
        """Prompt user for a default provider/profile"""
        auth = (self.config['username'],
                keyring.get_password(self.KEYRING_SERVICE, self.config['username']))
        profiles = requests.get(self.config['url']+"profiles/", auth=auth, verify=False).json()['results']

        print("Choose a default profile:")

        idx = 0
        for profile in profiles:
            print(str(idx)+':')
            print('   '+profile['title'])
            print('   '+profile['description'])
            idx += 1

        print
        choice = int(raw_input("Enter the number of the profile you would like to choose: "))

        provider = requests.get(
            self.config['url']+"providers/{0}/".format(profiles[choice]['cloud_provider']),
            auth=auth,
            verify=False).json()

        self.config['profile'] = profiles[choice]['title']
        self.config['provider'] = provider['title']
        self.config['provider_type'] = provider['provider_type_name']

    def _save_config(self):
        with open(self.CFG_FILE, "w") as f:
            f.write(json.dumps(self.config))

    def _bootstrap_account(self):
        """Bootstrap the users account with public key"""

        if self.has_public_key:
            keep_public_key = raw_input(
                "Keep existing public key? (y,n)? ")
        else:
            keep_public_key = "n"

        if keep_public_key in ["y", "Y"]:
            return

        raw_public_key = raw_input(
            "What is your public key (either path to or contents of)? ")

        if os.path.exists(raw_public_key):
            public_key = open(raw_public_key, "r").read()
        elif os.path.exists(os.path.expanduser(raw_public_key)):
            public_key = open(os.path.expanduser(raw_public_key), "r").read()
        else:
            public_key = raw_public_key

        if not public_key or not public_key.startswith("ssh-rsa"):
            print(self.colorize("Unable to find valid public key", "red"))
        else:
            print("Setting public key")
            self.stacks.set_public_key(public_key)
            self.has_public_key = True 

    def _bootstrap_formulas(self):
        """Import and wait for formulas to become ready"""

        def _check_formulas():
            formulas = self.stacks.list_formulas()
            for formula in formulas:
                if formula.get("status") != "complete":
                    return False
            return True
                    
        formulas = self.bootstrap_data.get("formulas", [])
        print("Importing {0} formula{1}".format(
            len(formulas),
            "s" if len(formulas) == 0 or len(formulas) > 1 else ""))
        for name, url in formulas.iteritems():
            print(" - {0} // {1}".format(name, url))
            self.stacks.import_formula(url, public=False)

        sys.stdout.write("Waiting for formulas .")
        sys.stdout.flush()
        try:
            poll_and_wait(_check_formulas)
            sys.stdout.write(" done!\n")
        except TimeoutException:
            print(self.colorize(
                "\nTIMEOUT - formulas failed to finish importing, monitor with `formulas list`",
                "red"))
 
    def _bootstrap_blueprints(self):
        """Create blueprints"""

        blueprints = self.bootstrap_data.get("blueprints", [])

        print("Creating {0} blueprint{1}".format(len(blueprints),
            "s" if len(blueprints) == 0 or len(blueprints) > 1 else ""))
        for name, blueprint in blueprints.iteritems():
            print(" - {0} // {1}".format(name, blueprint))

            # Get the blueprints relative to the bootstrap config file
            self._create_blueprint([os.path.join(os.path.dirname(self.BOOTSTRAP_FILE), "blueprints",
                blueprint)], bootstrap=True)

