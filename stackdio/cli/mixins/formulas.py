from __future__ import print_function

import click

from stackdio.cli.utils import pass_client, print_summary


@click.group()
def formulas():
    """
    Perform actions on formulas
    """
    pass


@formulas.command(name='list')
@pass_client
def list_formulas(client):
    """
    List all formulas
    """
    click.echo('Getting formulas ... ')
    print_summary('Formula', client.list_formulas())


@formulas.command(name='import')
@pass_client
@click.argument('uri')
@click.option('-u', '--username', type=click.STRING, help='Git username')
@click.option('-p', '--password', type=click.STRING, prompt=True, hide_input=True,
              help='Git password')
def import_formula(client, uri, username, password):
    """
    Import a formula
    """
    if username and not password:
        raise click.UsageError('You must provide a password when providing a username')

    click.echo('Importing formula from {0}'.format(uri))
    formula = client.import_formula(uri, git_username=username, git_password=password)

    click.echo('Detail: {0}'.format(formula['status_detail']))


def get_formula_id(client, formula_uri):
    found_formulas = client.search_formulas(uri=formula_uri)

    if len(found_formulas) == 0:
        raise click.Abort('Formula "{0}" does not exist'.format(formula_uri))
    else:
        return found_formulas[0]['id']


@formulas.command(name='delete')
@pass_client
@click.argument('uri')
def delete_formula(client, uri):
    """
    Delete a formula
    """
    formula_id = get_formula_id(client, uri)

    click.confirm('Really delete formula {0}?'.format(uri), abort=True)

    client.delete_formula(formula_id)
