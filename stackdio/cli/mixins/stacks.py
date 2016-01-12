from __future__ import print_function

import click

from stackdio.cli.mixins.blueprints import get_blueprint_id
from stackdio.cli.utils import pass_client, print_summary, poll_and_wait
from stackdio.client.exceptions import StackException


REQUIRE_ACTION_CONFIRMATION = ['terminate']


@click.group()
def stacks():
    """
    Perform actions on stacks
    """
    pass


@stacks.command(name='list')
@pass_client
def list_stacks(client):
    """
    List all stacks
    """
    client = obj['client']

    click.echo('Getting stacks ... ')
    print_summary('Stack', client.list_stacks())


@stacks.command(name='launch')
@pass_client
@click.argument('blueprint_title')
@click.argument('stack_title')
def launch_stack(client, blueprint_title, stack_title):
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
@pass_client
@click.argument('stack_title')
@click.option('-l', '--length', type=click.INT, default=20, help='The number of entries to show')
def stack_history(client, stack_title, length):
    """
    Print recent history for a stack
    """
    client = obj['client']

    stack_id = get_stack_id(client, stack_title)
    history = client.get_stack_history(stack_id)
    for event in history[0:min(length, len(history))]:
        click.echo('[{created}] {level} // {event} // {status}'.format(**event))


@stacks.command(name='hostnames')
@pass_client
@click.argument('stack_title')
def stack_hostnames(client, stack_title):
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
@pass_client
@click.argument('stack_title')
def delete_stack(client, stack_title):
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
@pass_client
@click.argument('stack_title')
@click.argument('action')
def perform_action(client, stack_title, action):
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


def print_command_output(json_blob):
    for host in sorted(json_blob['std_out'], key=lambda x: x['host']):
        click.secho('{0}:'.format(host['host']), fg='green')
        click.echo(host['output'])
        click.echo()


@stacks.command(name='run')
@click.pass_context
@click.argument('stack_title')
@click.argument('host_target')
@click.argument('command')
@click.option('-w', '--wait', is_flag=True, default=False,
              help='Wait for the command to finish running')
@click.option('-t', '--timeout', type=click.INT, default=120,
              help='The amount of time to wait for the command in seconds.  '
                   'Ignored if used without the -w option.')
def run_command(ctx, stack_title, host_target, command, wait, timeout):
    """
    Run a command on all hosts in the stack
    """
    client = ctx.obj['client']

    stack_id = get_stack_id(client, stack_title)

    resp = client.run_command(stack_id, host_target, command)

    if not wait:
        # Grab the parent info name
        name = ctx.parent.parent.info_name

        click.echo('Command "{0}" running on "{1}" hosts.  '
                   'Check the status by running:'.format(command, host_target))
        click.echo()
        click.secho('   {0} stacks command-output {1}'.format(name, resp['id']), fg='yellow')
        click.echo()
        return

    @poll_and_wait
    def check_status():
        command_out = client.get_command(resp['id'])

        if command_out['status'] != 'finished':
            return False

        click.echo()
        print_command_output(command_out)

        return True

    check_status(max_time=timeout)


@stacks.command(name='command-output')
@pass_client
@click.argument('command_id')
def get_command_output(client, command_id):
    """
    Get the status and output of a command
    """
    client = obj['client']

    resp = client.get_command(command_id)

    if resp['status'] != 'finished':
        click.secho('Status: {0}'.format(resp['status']), fg='yellow')
        return

    print_command_output(resp)


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
@pass_client
@click.argument('stack_title')
def list_stack_logs(client, stack_title):
    """
    Get a list of stack logs
    """
    client = obj['client']

    stack_id = get_stack_id(client, stack_title)

    print_logs(client, stack_id)


@stacks.command(name='logs')
@pass_client
@click.argument('stack_title')
@click.argument('log_type')
@click.option('-l', '--lines', type=click.INT, default=25, help='number of lines to tail')
def stack_logs(client, stack_title, log_type, lines):
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
