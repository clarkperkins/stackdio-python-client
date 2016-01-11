from __future__ import print_function

import click
from cmd2 import Cmd

from stackdio.cli.mixins.blueprints import get_blueprint_id
from stackdio.cli.utils import print_summary
from stackdio.client.exceptions import StackException


REQUIRE_ACTION_CONFIRMATION = ['terminate']


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


@stacks.command(name='hostnames')
@click.pass_obj
@click.argument('stack_title')
def stack_hostnames(obj, stack_title):
    """
    Print hostnames for a stack
    """
    client = obj['client']

    stack_id = get_stack_id(client, stack_title)
    hosts = client.get_stack_hosts(stack_id)

    click.echo('Hostnames:')
    for host in hosts:
        click.echo('  - {0} ({1})'.format(host['fqdn'], host['state']))


@stacks.command(name='delete')
@click.pass_obj
@click.argument('stack_title')
def delete_stack(obj, stack_title):
    """
    Delete a stack.  PERMANENT AND DESTRUCTIVE!!!
    """
    client = obj['client']

    stack_id = get_stack_id(client, stack_title)

    click.confirm('Really delete stack {0}?'.format(stack_title), abort=True)

    results = client.delete_stack(stack_id)
    click.echo('Delete stack results: \n{0}'.format(results))
    click.secho('Run "stacks history {0}" to monitor status of the deletion'.format(stack_title),
                fg='green')


@stacks.command(name='action')
@click.pass_obj
@click.argument('stack_title')
@click.argument('action')
def perform_action(obj, stack_title, action):
    """
    Perform an action on a stack
    """
    client = obj['client']

    stack_id = get_stack_id(client, stack_title)

    # Prompt for confirmation if need be
    if action in REQUIRE_ACTION_CONFIRMATION:
        click.confirm('Really {0} stack {1}?'.format(action, stack_title), abort=True)

    try:
        client.do_stack_action(stack_id, action)
    except StackException as e:
        raise click.UsageError(e.message)


@stacks.command(name='run')
@click.pass_obj
@click.argument('stack_title')
@click.argument('command')
@click.option('-w', '--wait', is_flag=True, help='Wait for the command to finish running')
def run_command(obj, stack_title, command, wait):
    """
    Run a command on all hosts in the stack
    """
    pass


def print_logs(client, stack_id):
    logs = client.list_stack_logs(stack_id)

    click.echo('Latest:')
    for log in logs['latest']:
        click.echo('  {0}'.format(log.split('/')[-1]))

    click.echo()

    click.echo('Historical:')
    for log in logs['historical']:
        click.echo('  {0}'.format(log.split('/')[-1]))


@stacks.command(name='list-logs')
@click.pass_obj
@click.argument('stack_title')
def list_stack_logs(obj, stack_title):
    """
    Get a list of stack logs
    """
    client = obj['client']

    stack_id = get_stack_id(client, stack_title)

    print_logs(client, stack_id)


@stacks.command(name='logs')
@click.pass_obj
@click.argument('stack_title')
@click.argument('log_type')
@click.option('-l', '--lines', type=click.INT, default=25, help='number of lines to tail')
def stack_logs(obj, stack_title, log_type, lines):
    """
    Get logs for a stack
    """
    client = obj['client']

    stack_id = get_stack_id(client, stack_title)

    split_arg = log_type.split('.')

    valid_log = True

    if len(split_arg) != 3:
        valid_log = False

    if valid_log:
        try:
            log_text = client.get_logs(stack_id, log_type=split_arg[0], level=split_arg[1],
                                       date=split_arg[2], tail=lines)
            click.echo(log_text)
        except StackException:
            valid_log = True

    if not valid_log:
        click.echo('Please use one of these logs:\n')

        print_logs(client, stack_id)

        raise click.UsageError('Invalid log')


class StackMixin(Cmd):

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
