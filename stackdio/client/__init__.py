import json
import logging
import os

from .http import HttpMixin, use_admin_auth, endpoint
from .exceptions import StackException

logger = logging.getLogger(__name__)


class StackdIO(HttpMixin):

    def __init__(self,
                 protocol="https",
                 host="localhost",
                 port=443,
                 base_url=None,
                 auth=None,
                 auth_admin=None,
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


    @use_admin_auth
    @endpoint("providers/")
    def create_provider(self, **kwargs):
        """Create a provider"""

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

        return self._post(endpoint, data=json.dumps(form_data), jsonify=True)


    @endpoint("providers/")
    def get_provider(self, title, provider_name):
        """Look for and return a provider"""

        result = self._get(endpoint, jsonify=True)
        for provider in result['results']:
            if provider.get("title") == title and \
               provider.get("provider_type_name") == provider_name:

                return provider

        raise StackException("Provider %s not found" % title)


    @use_admin_auth
    @endpoint("providers/")
    def create_profile(self, title, image_id, ssh_user, cloud_provider,
                       default_instance_size=None):
        """Create a profile"""
        data = {
            "title": title,
            "image_id": image_id,
            "ssh_user": ssh_user,
            "cloud_provider": cloud_provider,
            "default_instance_size": default_instance_size
        }
        return self._post(endpoint, data=json.dumps(data), jsonify=True)


    @endpoint("profiles/")
    def get_profile(self, title, cloud_provider):
        """Look for and return a profile"""

        result = self._get(endpoint, jsonify=True)

        for profile in result['results']:
            if profile.get("title") == title and \
               profile.get("cloud_provider") == cloud_provider:
                return profile

        return None


    @endpoint("formulas/")
    def import_formula(self, formula_uri, public=True):
        """Import a formula"""
        data = {
            "uri": formula_uri,
            "public": public,
        }
        return self._post(endpoint, data=json.dumps(data), jsonify=True)


    @endpoint("blueprints/")
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

        return self._post(endpoint, data=json.dumps(blueprint), jsonify=True)


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


    @endpoint("formulas/")
    def get_formulas(self):
        """Return all formulas"""
        return self._get(endpoint, jsonify=True)['results']


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


    @endpoint("providers/")
    def get_provider_id(self, slug, title=False):
        """Get the id for a provider that matches slug. If title is True will
        look at title instead."""

        result = self._get(endpoint, jsonify=True)

        for provider in result['results']:
            if provider.get("slug" if not title else "title") == slug:
                return provider.get("id")

        raise StackException("Provider %s not found" % slug)


    @endpoint("profiles/")
    def get_profile_id(self, slug, title=False):
        """Get the id for a profile that matches slug. If title is True will look
        at title instead."""

        result = self._get(endpoint, jsonify=True)

        for profile in result['results']:
            if profile.get("slug" if not title else "title") == slug:
                return profile.get("id")

        return StackException("Provider %s not found" % slug)


    @endpoint("stacks/")
    def get_stacks(self):
        """Return a list of all stacks"""
        return self._get(endpoint, jsonify=True)['results']


    @endpoint("stacks/{stack_id}/")
    def get_stack(self, stack_id):
        """Get stack info"""
        result = self._get(endpoint, none_on_404=True, jsonify=True)
        if result is None:
            raise StackException("Stack %s not found" % stack_id)
        else:
            return result


    @endpoint("stacks/{stack_id}/history/")
    def get_stack_history(self, stack_id):
        """Get stack info"""
        result = self._get(endpoint, none_on_404=True, jsonify=True)
        if result is None:
            raise StackException("Stack %s not found" % stack_id)
        else:
            return result


    @endpoint("stacks/")
    def get_stack_id(self, title):
        """Find a stack id"""

        result = self._get(endpoint, jsonify=True)
        try:
            for stack in result['results']:
                if stack.get("title") == title:
                    return stack.get("id")
        except TypeError, e:
            logger.error("Error querying stacks: %s", e)

        raise StackException("Stack %s not found" % title)


    @endpoint("stacks/{stack_id}/hosts/")
    def get_stack_hosts(self, stack_id):
        """Get a list of all stack hosts"""
        return self._get(endpoint, jsonify=True)['results']


    @endpoint("blueprints/{blueprint_id}/")
    def get_blueprint(self, blueprint_id):
        """Return info for a specific blueprint_id"""
        return self._get(endpoint, jsonify=True)


    @endpoint("blueprints/")
    def get_blueprint_id(self, title):
        """Get the id for a blueprint that matches title"""
        result = self._get(endpoint, params={"title": title}, jsonify=True)

        if not result.get('count') == 1:
            raise StackException("Blueprint %s not found" % title)

        return result['results'][0]['id']


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


    @endpoint("provider_types/")
    def get_provider_type(self, type_name):
        """Get the id for the provider specified by type_name"""

        result = self._get(endpoint, jsonify=True)
        for provider_type in result['results']:
            if provider_type.get("type_name") == type_name:
                return provider_type.get("id")

        raise StackException("Provider type %s not found" % type_name)


    @endpoint("zones/")
    def get_zone(self, title, type_name="ec2"):
        """Get a zone id for title"""

        provider_type = self.get_provider_type(type_name)
        result = self._get(endpoint, jsonify=True)
        for zone in result['results']:
            if zone.get("title") == title and \
               zone.get("provider_type") == provider_type:
                return zone.get("id")

        raise StackException("Zone %s not found for %s" % (title, type_name))


    @endpoint("stacks/")
    def launch_stack(self, stack_data):
        """Launch a stack as described by stack_data"""
        return self._post(endpoint, data=json.dumps(stack_data), jsonify=True)['results']


    @endpoint("stacks/{stack_id}/hosts/")
    def describe_hosts(self, stack_id, key="fqdn", ec2=False):
        """Retrieve a list of info about a stack. Defaults to the id for each
        host, but you can specify any available key. Setting ec2=True will
        force it to inspect the ec2_metadata field."""

        EC2 = "ec2_metadata"
        result = self._get(endpoint, jsonify=True)

        stack_details = []

        for host in result['results']:
            if not ec2:
                host_details = host.get(key)
            else:
                host_details = host.get(EC2).get(key)

            if host_details:
                stack_details.append(host_details)

        if stack_details:
            return stack_details

        raise StackException("Key %s for stack %s not available" % (key, stack_id))


    @endpoint("stacks/{stack_id}/")
    def delete_stack(self, stack_id):
        """Destructively delete a stack forever."""
        # make sure the stack exists
        self.get_stack(stack_id)
        return self._delete(endpoint, jsonify=True)


    @endpoint("stacks/{stack_id}/action/")
    def get_valid_actions(self, stack_id):
        return self._get(endpoint, jsonify=True)['available_actions']


    @endpoint("stacks/{stack_id}/action/")
    def do_action(self, stack_id, action):
        """Execute an action on a stack"""
        valid_actions = self.get_valid_actions(stack_id)

        if action not in valid_actions:
            raise StackException("Invalid action, must be one of %s" %
                                 ", ".join(valid_actions))

        data = {"action": action}

        return self._post(endpoint, data=json.dumps(data), jsonify=True)
