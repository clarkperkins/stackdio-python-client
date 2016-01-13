#!/usr/bin/env python

import os

import click

from stackdio.cli.mixins import blueprints, formulas, stacks
from stackdio.cli.utils import pass_client
from stackdio.client import StackdioClient
from stackdio.client.config import CFG_FILE
from stackdio.client.version import __version__


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

HIST_FILE = os.path.join(os.path.expanduser('~'), '.stackdio-cli', 'history')


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-v', '--version')
@click.option('-c', '--config-file', help='The config file to use.',
              type=click.Path(dir_okay=False, file_okay=True), default=CFG_FILE,
              envvar='STACKDIO_CLI_CONFIG_FILE')
@click.pass_context
def stackdio(ctx, config_file):
    # Create a client instance
    client = StackdioClient(cfg_file=config_file)

    # Throw an error if we're not configured already
    if ctx.invoked_subcommand not in ('configure', None) and not client.usable():
        raise click.UsageError('It looks like you haven\'t used this CLI before.  Please run '
                               '`stackdio-cli configure`')

    # Put the client in the obj so other commands can pick it up
    ctx.obj = client


@stackdio.command(name='configure')
@pass_client
def configure(client):
    """
    Configure the client
    """
    client.config.prompt_for_config()


@stackdio.command(name='server-version')
@pass_client
def server_version(client):
    """
    Print the version of the server
    """
    click.echo('stackdio-server, version {0}'.format(client.get_version()))


# Add all our other commands
stackdio.add_command(blueprints.blueprints)
stackdio.add_command(stacks.stacks)
stackdio.add_command(formulas.formulas)


def main():
    # Just run our CLI tool
    stackdio()


if __name__ == '__main__':
    main()
