import json

from .exceptions import StackException
from .http import HttpMixin, endpoint
from .version import accepted_versions, deprecated


class StackMixin(HttpMixin):

    @endpoint("stacks/")
    def create_stack(self, stack_data):
        """Launch a stack as described by stack_data"""
        return self._post(endpoint, data=json.dumps(stack_data), jsonify=True)


    @endpoint("stacks/")
    def list_stacks(self):
        """Return a list of all stacks"""
        return self._get(endpoint, jsonify=True)['results']


    @endpoint("stacks/{stack_id}/")
    def get_stack(self, stack_id):
        """Get stack info"""
        return self._get(endpoint, jsonify=True)


    @endpoint("stacks/")
    def search_stacks(self, *kwargs):
        """Search for stacks that match the given criteria"""
        return self._get(endpoint, params=kwargs, jsonify=True)['results']


    @endpoint("stacks/{stack_id}/")
    def delete_stack(self, stack_id):
        """Destructively delete a stack forever."""
        return self._delete(endpoint, jsonify=True)


    @endpoint("stacks/{stack_id}/action/")
    def get_valid_stack_actions(self):
        return self._get(endpoint, jsonify=True)['available_actions']


    @endpoint("stacks/{stack_id}/action/")
    def do_stack_action(self, stack_id, action):
        """Execute an action on a stack"""
        valid_actions = self.get_valid_actions(stack_id)

        if action not in valid_actions:
            raise StackException("Invalid action, must be one of %s" %
                                 ", ".join(valid_actions))

        data = {"action": action}

        return self._post(endpoint, data=json.dumps(data), jsonify=True)


    @endpoint("stacks/{stack_id}/history/")
    def get_stack_history(self, stack_id):
        """Get stack info"""
        result = self._get(endpoint, none_on_404=True, jsonify=True)
        if result is None:
            raise StackException("Stack %s not found" % stack_id)
        else:
            return result


    @deprecated
    @accepted_versions("<0.7")
    def get_stack_id(self, title):
        """Find a stack id"""

        stacks = self.list_stacks()
        for stack in stacks:
            if stack.get("title") == title:
                return stack.get("id")

        raise StackException("Stack %s not found" % title)


    @endpoint("stacks/{stack_id}/hosts/")
    def get_stack_hosts(self, stack_id):
        """Get a list of all stack hosts"""
        return self._get(endpoint, jsonify=True)['results']


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
