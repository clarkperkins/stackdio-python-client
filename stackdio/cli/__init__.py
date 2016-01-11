#!/usr/bin/env python

from __future__ import print_function

import os

import click

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
    """
    Configure the client
    """
    client = obj['client']
    print('configuring')


@stackdio.command('server-version')
@click.pass_obj
def server_version(obj):
    """
    Print the version of the server
    """
    client = obj['client']
    click.echo('stackdio-server, version {0}'.format(client.get_version()))


# Add all our other commands
stackdio.add_command(blueprints.blueprints)
stackdio.add_command(stacks.stacks)


def main():
    # Just run our CLI tool
    stackdio(obj={})


if __name__ == '__main__':
    main()
