from __future__ import print_function

import json

import click
from cmd2 import Cmd

from stackdio.cli.mixins.blueprints import get_blueprint_id
from stackdio.cli.utils import print_summary
from stackdio.client.exceptions import StackException


@click.group()
def stacks():
    """
    Perform actions on stacks
    """
    pass


@stacks.command(name='list')
@click.pass_obj
def list_stacks(obj):
    """
    List all stacks
    """
    client = obj['client']

    click.echo('Getting stacks ... ')
    print_summary('Stack', client.list_stacks())


@stacks.command(name='launch')
@click.pass_obj
@click.argument('blueprint_title')
@click.argument('stack_title')
def launch_stack(obj, blueprint_title, stack_title):
        """
        Launch a stack from a blueprint
        """
        client = obj['client']

        blueprint_id = get_blueprint_id(client, blueprint_title)

        click.echo('Launching stack "{0}" from blueprint "{1}"'.format(stack_title,
                                                                       blueprint_title))

        stack_data = {
            'blueprint': blueprint_id,
            'title': stack_title,
            'description': 'Launched from blueprint %s' % (blueprint_title),
            'namespace': stack_title,
        }
        results = client.create_stack(stack_data)
        click.echo('Stack launch results:\n{0}'.format(results))


def get_stack_id(client, stack_title):
    found_stacks = client.search_stacks(title=stack_title)

    if len(found_stacks) == 0:
        raise click.Abort('Stack "{0}" does not exist'.format(stack_title))
    elif len(found_stacks) > 1:
        raise click.Abort('Multiple stacks matching "{0}" were found'.format(stack_title))
    else:
        return found_stacks[0]['id']


@stacks.command(name='history')
@click.pass_obj
@click.argument('stack_title')
@click.option('-l', '--length', type=click.INT, default=20, help='The number of entries to show')
def stack_history(obj, stack_title, length):
    """
    Print recent history for a stack
    """
    client = obj['client']

    stack_id = get_stack_id(client, stack_title)
    history = client.get_stack_history(stack_id)
    for event in history[0:min(length, len(history))]:
        click.echo('[{created}] {level} // {event} // {status}'.format(**event))


class StackMixin(Cmd):

    STACK_ACTIONS = ["start", "stop", "launch_existing", "terminate", "provision", "custom"]
    STACK_COMMANDS = ["list", "launch_from_blueprint", "history", "hostnames",
        "delete", "logs", "access_rules"] + STACK_ACTIONS

    VALID_LOGS = {
        "provisioning": "provisioning.log",
        "provisioning-error": "provisioning.err",
        "global-orchestration": "global_orchestration.log",
        "global-orchestration-error": "global_orchestration.err",
        "orchestration": "orchestration.log",
        "orchestration-error": "orchestration.err",
        "launch": "launch.log",
    }

    def do_stacks(self, arg):
        """Entry point to controlling."""

        USAGE = "Usage: stacks COMMAND\nWhere COMMAND is one of: %s" % (
            ", ".join(self.STACK_COMMANDS))

        # We don't want multiline commands, so include anything after a terminator as well
        args = arg.parsed.raw.split()[1:]
        if not args or args[0] not in self.STACK_COMMANDS:
            print(USAGE)
            return

        stack_cmd = args[0]

        if stack_cmd == "list":
            self._list_stacks()
        elif stack_cmd == "launch_from_blueprint":
            self._launch_stack(args[1:])
        elif stack_cmd == "history":
            self._stack_history(args[1:])
        elif stack_cmd == "hostnames":
            self._stack_hostnames(args[1:])
        elif stack_cmd == "delete":
            self._stack_delete(args[1:])
        elif stack_cmd == "logs":
            self._stack_logs(args[1:])
        elif stack_cmd == "access_rules":
            self._stack_access_rules(args[1:])
        elif stack_cmd in self.STACK_ACTIONS:
            self._stack_action(args)

        else:
            print(USAGE)

    def _stack_action(self, args):
        """Perform an action on a stack."""

        if len(args) == 1:
            print("Usage: stacks {0} STACK_NAME".format(args[0]))
            return
        elif args[0] != "custom" and len(args) != 2:
            print("Usage: stacks ACTION STACK_NAME")
            print("Where ACTION is one of {0}".format(
                ", ".join(self.STACK_ACTIONS)))
            return
        elif args[0] == "custom" and len(args) < 4:
            print("Usage: stacks custom STACK_NAME HOST_TARGET COMMAND")
            print("Where command can be arbitrarily long with spaces")
            return

        if args[0] not in self.STACK_ACTIONS:
            print(self.colorize(
                "Invalid action - must be one of {0}".format(self.STACK_ACTIONS),
                "red"))
            return

        action = "launch" if args[0] == "launch_existing" else args[0]
        stack_name = args[1]

        if action == "terminate":
            really = raw_input("Really terminate stack {0} (y/n)? ".format(args[0]))
            if really not in ["y", "Y"]:
                print("Aborting termination")
                return

        if action == "custom":
            host_target = args[2]
            command = ''
            for token in args[3:]:
                command += token + ' '

        stack_id = self._get_stack_id(stack_name)
        print("Performing [{0}] on [{1}]".format(
            action, stack_name))

        if action == "custom":
            results = self.stacks.do_stack_action(stack_id, "custom", host_target, command)
        else:
            results = self.stacks.do_stack_action(stack_id, action)
        print("Stack action results:\n{0}".format(json.dumps(results, indent=3)))

    def _stack_hostnames(self, args):
        """Print hostnames for a stack"""

        if len(args) < 1:
            print("Usage: stacks hostnames STACK_NAME")
            return

        stack_id = self._get_stack_id(args[0])
        try:
            fqdns = self.stacks.describe_hosts(stack_id)
        except StackException:
            print(self.colorize(
                "Hostnames not available - stack still launching?", "red"))
            raise

        print("Hostnames:")
        for host in fqdns:
            print("  - {0}".format(host))

    def _stack_delete(self, args):
        """Delete a stack.  PERMANENT AND DESTRUCTIVE!!!"""

        if len(args) < 1:
            print("Usage: stacks delete STACK_NAME")
            return

        stack_id = self._get_stack_id(args[0])
        really = raw_input("Really delete stack {0} (y/n)? ".format(args[0]))
        if really not in ["y", "Y"]:
            print("Aborting deletion")
            return

        results = self.stacks.delete_stack(stack_id)
        print("Delete stack results: {0}".format(results))
        print(self.colorize(
            "Run 'stacks history {0}' to monitor status of the deletion".format(
            args[0]),
            "green"))

    def _stack_logs(self, args):
        """Get logs for a stack"""

        MAX_LINES = 25

        if len(args) < 2:
            print("Usage: stacks logs STACK_NAME LOG_TYPE [LOG_LENGTH]")
            print("LOG_TYPE is one of {0}".format(
                ", ".join(self.stacks.VALID_LOGS.keys())))
            print("This defaults to the last {0} lines of the log.".
                format(MAX_LINES))
            return

        if len(args) >= 3:
            max_lines = args[2]
        else:
            max_lines = MAX_LINES

        stack_id = self.stacks.get_stack_id(args[0])

        split_arg = self.VALID_LOGS[args[1]].split('.')

        log_text = self.stacks.get_logs(stack_id, log_type=split_arg[0], level=split_arg[1],
                                        tail=max_lines)
        print(log_text)

    def _stack_access_rules(self, args):
        """Get access rules for a stack"""

        COMMANDS = ["list", "add", "delete"]

        if len(args) < 2 or args[0] not in COMMANDS:
            print("Usage: stacks access_rules COMMAND STACK_NAME")
            print("Where COMMAND is one of: %s" % (", ".join(COMMANDS)))
            return

        if args[0] == "list":
            stack_id = self.stacks.get_stack_id(args[1])
            groups = self.stacks.list_access_rules(stack_id)
            print("## {0} Access Groups".format(len(groups)))
            for group in groups:
                print("- Name: {0}".format(group['blueprint_host_definition']['title']))
                print("  Description: {0}".format(group['blueprint_host_definition']['description']))
                print("  Rules:")
                for rule in group['rules']:
                    print("    {0}".format(rule['protocol']), end='')
                    if rule['from_port'] == rule['to_port']:
                        print("port {0} allows".format(rule['from_port']), end='')
                    else:
                        print("ports {0}-{1} allow".format(rule['from_port'],
                                                           rule['to_port']), end='')
                    print(rule['rule'])
                print('')
            return

        elif args[0] == "add":
            if len(args) < 3:
                print("Usage: stacks access_rules add STACK_NAME GROUP_NAME")
                return

            stack_id = self.stacks.get_stack_id(args[1])
            group_id = self.stacks.get_access_rule_id(stack_id, args[2])

            protocol = raw_input("Protocol (tcp, udp, or icmp): ")
            from_port = raw_input("From port: ")
            to_port = raw_input("To port: ")
            rule = raw_input("Rule (IP address or group name): ")

            data = {
                "action": "authorize",
                "protocol": protocol,
                "from_port": from_port,
                "to_port": to_port,
                "rule": rule
            }

            self.stacks.edit_access_rule(group_id, data)

        elif args[0] == "delete":
            if len(args) < 3:
                print("Usage: stacks access_rules delete STACK_NAME GROUP_NAME")
                return

            stack_id = self.stacks.get_stack_id(args[1])
            group_id = self.stacks.get_access_rule_id(stack_id, args[2])

            index = 0

            rules = self.stacks.list_rules_for_group(group_id)

            print('')
            for rule in rules:
                print("{0}) {1}".format(index, rule['protocol']), end='')
                if rule['from_port'] == rule['to_port']:
                    print("port {0} allows".format(rule['from_port']), end='')
                else:
                    print("ports {0}-{1} allow".format(rule['from_port'], rule['to_port']), end='')
                print(rule['rule'])
                index += 1
            print('')
            delete_index = int(raw_input("Enter the index of the rule to delete: "))

            data = rules[delete_index]
            data['from_port'] = int(data['from_port'])
            data['to_port'] = int(data['to_port'])
            data['action'] = "revoke"

            self.stacks.edit_access_rule(group_id, data)

        print('')

        args[0] = "list"

        self._stack_access_rules(args)
