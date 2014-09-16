
#
# A simple module for interacting with an instance of stackd.io.
#
# CAVEAT EMPTOR: This is not something that will be used permanently, it's more
# of a testing ground for figuring out how stackd.io works. It may be committed
# in QATP, but will not be long lived in its current form. For example, it is
# hard coding a number of assumptions that will need to be abstracted out into
# a more general purpose library for using stackd.io.
#

from simplejson import JSONDecodeError
import json
import os
import logging
from urlparse import urljoin

import requests

logger = logging.getLogger(__name__)

# verbose logging for requests
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.ERROR)
requests_log.propagate = True

# hack to enable verbose logging for requests
if os.getenv("VERBOSE_REQUESTS"):
    import httplib
    httplib.HTTPConnection.debuglevel = 1
    requests_log.setLevel(logging.DEBUG)

class StackException(Exception):
    pass
class NoAdminException(Exception):
    pass

T1MICRO = 14

class StackdIO():

    JSON_HEADER = {"content-type":"application/json"}
    VALID_ACTIONS = ["stop", "start", "terminate", "launch", "provision"]

    def __init__(self, base_url, auth, auth_admin=None, verify_ssl=False):
        """auth_admin is optional, only needed for creating provider, profile,
        and base security groups"""

        self.base_url = base_url
        self.auth = auth
        self.auth_admin = auth_admin
        self.verify_ssl = verify_ssl

    def _get(self, url, auth=None, params=None):
        """Make a GET request"""

        # @todo need to handle pagination properly here, just punting with a
        # large page_size for now
        auth = self.auth if not auth else auth
        params = params if params is not None else { 'page_size' : 100 }

        r = requests.get(urljoin(self.base_url, url),
                         auth=auth, headers=self.JSON_HEADER, verify=self.verify_ssl,
                         params=params)
        return r

    def _post(self, url, data=None, headers=None, auth=None):
        """Make a POST request"""

        if headers is None:
            headers = self.JSON_HEADER

        auth = self.auth if not auth else auth
        r = requests.post(urljoin(self.base_url, url), auth=auth,
            data=json.dumps(data) if data else None,
            headers=headers, verify=self.verify_ssl)
        return r

    def _put(self, url, data=None, auth=None, headers=None):
        """Make a PUT request"""

        if headers is None:
            headers = self.JSON_HEADER

        auth = self.auth if not auth else auth
        r = requests.put(urljoin(self.base_url, url), auth=auth,
            data=json.dumps(data) if data else None,
            headers=headers, verify=self.verify_ssl)
        return r

    def _delete(self, url, data=None, auth=None, headers=None):
        """Make a DELETE request"""

        if headers is None:
            headers = self.JSON_HEADER

        auth = self.auth if not auth else auth
        r = requests.delete(urljoin(self.base_url, url), auth=auth,
            data=json.dumps(data) if data else None,
            headers=headers, verify=self.verify_ssl)
        return r

    def create_provider(self, **kwargs):
        """Create a provider"""

        if not self.auth_admin:
            raise NoAdminException("No admin credentials were specified")

        form_data = {
            "title": None,
            "account_id": None,
            "provider_type": None,
            "access_key_id": None,
            "secret_access_key": None,
            "keypair": None,
            "security_groups": None,
            "route53_domain": None,
            "default_availability_zone": None,
            "private_key": None
        }

        for key in form_data.keys():
            form_data[key] = kwargs.get(key)

        r = self._post("providers/", data=form_data, auth=self.auth_admin)
        logger.info("create_provider result:\n{0}".format(r.text))

    def get_provider(self, title, provider_name):
        """Look for and return a provider"""

        r = self._get("providers/")

        for provider in r.json()["results"]:
            if (provider.get("title") == title and
            provider.get("provider_type_name") == provider_name):
                return provider

        raise StackException("Provider %s not found" % title)

    def create_profile(self, title, image_id, ssh_user, cloud_provider,
    default_instance_size=T1MICRO):
        """Create a profile"""

        if not self.auth_admin:
            raise NoAdminException("No admin credentials were specified")

        data = {
            "title": title,
            "image_id": image_id,
            "ssh_user": ssh_user,
            "cloud_provider": cloud_provider,
            "default_instance_size": default_instance_size
        }
        r = self._post("profiles/", data=data, auth=self.auth_admin)
        logger.info("create_profile result:\n%s", r.text)

    def get_profile(self, title, cloud_provider):
        """Look for and return a profile"""

        r = self._get("profiles/")

        for profile in r.json()["results"]:
            if (profile.get("title") == title and
            profile.get("cloud_provider") == cloud_provider):
                return profile

        return None

    def import_formula(self, formula_uri, public=True):
        """Import a formula"""

        data = {
            "uri": formula_uri,
            "public": public,
        }
        r = self._post("formulas/", data=data)
        logger.info("import_formula result:\n%s", r.text)


    def create_blueprint(self, blueprint, provider="ec2"):
        """Create a blueprint"""

        # check the provided blueprint to see if we need to look up any ids
        for host in blueprint["hosts"]:
            if isinstance(host["size"], str):
                host["size"] = self.get_instance_id(host["size"], provider)

            if isinstance(host["zone"], str):
                host["zone"] = self.get_zone(host["zone"], provider)

            if isinstance(host["cloud_profile"], str):
                host["cloud_profile"] = self.get_profile_id(host["cloud_profile"])

            for component in host["formula_components"]:
                if isinstance(component["id"], (tuple, list)):
                    component["id"] = self.get_component_id(
                        self.get_formula(component["id"][0]),
                        component["id"][1])

        r = self._post("blueprints/", data=blueprint)
        logger.info("create blueprints result:\n%s", r.text)

    def create_security_group(self, name, description, cloud_provider, is_default=True):
        """Create a security group"""

        if not self.auth_admin:
            raise NoAdminException("No admin credentials were specified")

        data = {
            "name": name,
            "description": description,
            "cloud_provider": cloud_provider,
            "is_default": is_default
        }
        r = self._post("security_groups/", data=data, auth=self.auth_admin)
        logger.info("create_security_group result:\n%s", r.text)

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
        r = self._put("settings/", data=data)
        logger.info("set_public_key results:\n%s", r.text)

    def get_formulas(self):
        """Return all formulas"""

        r = self._get("formulas/")
        return r.json().get("results")

    def get_formula(self, title):
        """Get a formula that matches title"""

        for formula in self.get_formulas():
            if formula.get("title") == title:
                return formula

        raise StackException("Formula %s not found" % title)

    def get_formula_id(self, title):
        """Get the id for a formula that matches title. If component_title is
        provided, find and return the component id"""

        formula = self.get_formula(title)
        return formula.get("id")

    def get_component_id(self, formula, component_title):
        """Get the id for a component from formula_id that matches title"""

        for component in formula.get("components"):
            if component.get("title") == component_title:
                return component.get("id")

        raise StackException("Component %s not found for formula %s" %
            (component_title, formula.get("title")))

    def get_provider_id(self, slug, title=False):
        """Get the id for a provider that matches slug. If title is True will
        look at title instead."""

        r = self._get("providers/")

        for provider in r.json().get("results"):
            if provider.get("slug" if not title else "title") == slug:
                return provider.get("id")

        raise StackException("Provider %s not found" % slug)

    def get_profile_id(self, slug, title=False):
        """Get the id for a profile that matches slug. If title is True will look
        at title instead."""

        r = self._get("profiles/")

        for profile in r.json().get("results"):
            if profile.get("slug" if not title else "title") == slug:
                return profile.get("id")

        return StackException("Provider %s not found" % slug)

    def get_stacks(self):
        """Return a list of all stacks"""

        r = self._get("stacks/")
        try:
            return r.json().get("results")
        except JSONDecodeError, e:
            raise StackException("Unable to decode json;\nRequest results: %s\nException: %s",
                r.text, e)

    def get_stack(self, stack_id):
        """Get stack info"""

        r = self._get("stacks/%s/" % stack_id)
        if r.status_code >= 200 and r.status_code < 300:
            return r.json()

        raise StackException("Stack %s not found" % stack_id)

    def get_stack_history(self, stack_id):
        """Get stack info"""

        r = self._get("stacks/%s/history/" % stack_id)
        if r.status_code >= 200 and r.status_code < 300:
            return r.json()

        raise StackException("Stack %s not found" % stack_id)

    def get_stack_id(self, title):
        """Find a stack id"""

        r = self._get("stacks/")
        try:
            for stack in r.json().get("results"):
                if stack.get("title") == title:
                    return stack.get("id")
        except TypeError, e:
            logger.error("Error querying stacks: %s", e)

        raise StackException("Stack %s not found" % title)

    def get_stack_hosts(self, stack_id):
        """Get a list of all stack hosts"""

        r = self._get("stacks/%s/hosts/" % stack_id)
        try:
            return r.json().get("results")
        except JSONDecodeError, e:
            raise StackException("Unable to decode json;\nRequest results: %s\nException: %s",
                r.text, e)

    def get_blueprint(self, blueprint_id):
        """Return info for a specific blueprint_id"""

        r = self._get("blueprints/%s/" % blueprint_id)
        try:
            return r.json()
        except JSONDecodeError, e:
            raise StackException("Unable to decode json;\nRequest results: %s\nException: %s",
                r.text, e)

    def get_blueprint_id(self, title):
        """Get the id for a blueprint that matches title"""

        r = self._get("blueprints", params={"title" : title})
        if not r.json().get('count') == 1:
            raise StackException("Blueprint %s not found" % title)
        return r.json()['results'][0]['id']

    def get_instance_id(self, instance_id, provider_type="ec2"):
        """Get the id for an instance_id. The instance_id parameter is the
        provider name (e.g. m1.large). The id returned is the stackd.io id
        for use in API calls (e.g. 1)."""

        r = self._get("instance_sizes/")
        for instance in r.json().get("results"):
            if (instance.get("instance_id") == instance_id and
            instance.get("provider_type") == provider_type):
                return instance.get("id")

        raise StackException("Instance type %s from provider %s not found" % (
            instance_id, provider_type))

    def get_provider_type(self, type_name):
        """Get the id for the provider specified by type_name"""

        r = self._get("provider_types/")
        for provider_type in r.json().get("results"):
            if provider_type.get("type_name") == type_name:
                return provider_type.get("id")

        raise StackException("Provider type %s not found" % type_name)

    def get_zone(self, title, type_name="ec2"):
        """Get a zone id for title"""

        provider_type = self.get_provider_type(type_name)

        r = self._get("zones/")
        for zone in r.json().get("results"):
            if (zone.get("title") == title and
            zone.get("provider_type") == provider_type):
                return zone.get("id")

        raise StackException("Zone %s not found for %s" % (title, type_name))

    def launch_stack(self, stack_data):
        """Launch a stack as described by stack_data"""

        r = self._post("stacks/", data=stack_data)
        logger.info("launch_stack result:\n%s", r.text)
        return r.json()

    def describe_hosts(self, stack_id, key="fqdn", ec2=False, criteria=None):
        """Retrieve a list of info about a stack. Defaults to the fqdn for each
        host, but you can specify any available key. Setting ec2=True will
        force it to inspect the ec2_metadata field."""

        EC2 = "ec2_metadata"

        r = self._get("stacks/{0}/hosts/".format(stack_id))
        r.raise_for_status()

        stack_details = []

        for host in r.json().get("results"):
            if not ec2:
                host_details = host.get(key)
            else:
                host_details = host.get(EC2).get(key)

            if host_details:
                stack_details.append(host_details)

        if stack_details:
            return stack_details

        raise StackException("Key %s for stack %s not available" % (key, stack_id))

    def delete_stack(self, stack_id):
        """Destructively delete a stack forever."""

        # make sure the stack exists
        self.get_stack(stack_id)

        r = self._delete("stacks/{0}/".format(stack_id))
        return r.json()

    def do_action(self, stack_id, action):
        """Execute an action on a stack"""

        if action not in self.VALID_ACTIONS:
            raise StackException("Invalid action, must be one of %s" %
                ", ".join(self.VALID_ACTIONS))

        data = {"action": action}
        r = self._post("stacks/{0}/action/".format(stack_id), data=data)
        return r
