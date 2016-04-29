
import json
import os

import click
import yaml

from stackdio.cli.blueprints.generator import BlueprintGenerator, BlueprintException
from stackdio.cli.utils import print_summary, pass_client


class BlueprintNotFound(Exception):
    pass


@click.group()
def blueprints():
    """
    Perform actions on blueprints
    """
    pass


@blueprints.command(name='list')
@pass_client
def list_blueprints(client):
    """
    List all blueprints
    """
    click.echo('Getting blueprints ... ')
    print_summary('Blueprint', client.list_blueprints())


def _recurse_dir(dirname, extensions, prefix=''):
    for template in os.listdir(dirname):
        if os.path.isdir(os.path.join(dirname, template)):
            # Recursively look at the subdirectories
            _recurse_dir(os.path.join(dirname, template),
                         extensions,
                         prefix + template + os.sep)
        elif template.split('.')[-1] in extensions and not template.startswith('_'):
            click.echo('    {0}'.format(prefix + template))


@blueprints.command(name='list-templates')
@pass_client
def list_templates(client):
    """
    List all the blueprint templates
    """
    if 'blueprint_dir' not in client.config:
        click.echo('Missing blueprint directory config')
        return

    try:
        blueprint_dir = os.path.expanduser(client.config['blueprint_dir'])
    except KeyError:
        raise click.UsageError('Missing \'blueprint_dir\' in config.  Please run `configure`.')

    click.echo('Template mappings:')
    mapping = yaml.safe_load(open(os.path.join(blueprint_dir, 'mappings.yaml'), 'r'))
    if mapping:
        for blueprint in mapping:
            click.echo('    {0}'.format(blueprint))

    click.echo()

    click.echo('Templates:')
    _recurse_dir(os.path.join(blueprint_dir, 'templates'), ['json'])

    click.echo()

    click.echo('Var files:')
    _recurse_dir(os.path.join(blueprint_dir, 'var_files'), ['yaml', 'yml'])


def _create_single_blueprint(config, template_file, var_files, no_prompt, extra_vars=None):
    blueprint_dir = os.path.expanduser(config['blueprint_dir'])

    gen = BlueprintGenerator([os.path.join(blueprint_dir, 'templates')])

    if not os.path.exists(os.path.join(blueprint_dir, 'templates', template_file)):
        click.secho('You gave an invalid template', fg='red')
        return

    if template_file.startswith('_'):
        click.secho('WARNING: Templates beginning with \'_\' are generally not meant to '
                    'be used directly.  Please be sure this is really what you want.\n',
                    fg='magenta')

    final_var_files = []

    # Build a list with full paths in it instead of relative paths
    for var_file in var_files:
        var_file = os.path.join(blueprint_dir, 'var_files', var_file)
        if os.path.exists(var_file):
            final_var_files.append(open(var_file, 'r'))
        else:
            click.secho('WARNING: Variable file {0} was not found.  Ignoring.'.format(var_file),
                        fg='magenta')

    # Generate the JSON for the blueprint
    return gen.generate(template_file,
                        final_var_files,  # Pass in a list
                        variables=extra_vars,
                        prompt=no_prompt)


@blueprints.command(name='create')
@pass_client
@click.option('-m', '--mapping',
              help='The entry in the map file to use')
@click.option('-t', '--template',
              help='The template file to use')
@click.option('-v', '--var-file', multiple=True,
              help='The variable files to use.  You may pass in more than one.  They '
                   'will be loaded from left to right, so variables in the rightmost '
                   'var files will override those in var files to the left.')
@click.option('-n', '--no-prompt', is_flag=True, default=True,
              help='Don\'t prompt for missing variables in the template')
def create_blueprint(client, mapping, template, var_file, no_prompt):
    """
    Create a blueprint
    """
    if not template and not mapping:
        raise click.UsageError('You must specify either a template or a mapping.')

    click.secho('Advanced users only - use the web UI if this isn\'t you!\n', fg='green')

    try:
        blueprint_dir = client.config['blueprint_dir']
    except KeyError:
        raise click.UsageError('Missing \'blueprint_dir\' in config.  Please run `configure`.')

    if mapping:
        mappings = yaml.safe_load(open(os.path.join(blueprint_dir, 'mappings.yaml'), 'r'))
        if not mappings or mapping not in mappings:
            click.secho('You gave an invalid mapping.', fg='red')
            return
        else:
            template = mappings[mapping].get('template')
            var_file = mappings[mapping].get('var_files', [])
            if not template:
                click.secho('Your mapping must specify a template.', fg='red')
                return

    bp_json = _create_single_blueprint(client.config, template, var_file, no_prompt)

    if not bp_json:
        # There was an error with the blueprint creation, and there should already be an
        # error message printed
        return

    click.echo('Creating blueprint')

    r = client.create_blueprint(bp_json, raise_for_status=False)
    click.echo(json.dumps(r, indent=2))


@blueprints.command(name='create-all')
@pass_client
@click.confirmation_option('-y', '--yes', prompt='Really create all blueprints?')
def create_all_blueprints(client):
    """
    Create all the blueprints in the map file
    """
    try:
        blueprint_dir = os.path.expanduser(client.config['blueprint_dir'])
    except KeyError:
        raise click.UsageError('Missing \'blueprint_dir\' in config.  Please run `configure`.')
    mapping = yaml.safe_load(open(os.path.join(blueprint_dir, 'mappings.yaml'), 'r'))

    for name, vals in mapping.items():
        try:
            bp_json = _create_single_blueprint(client.config, vals['template'],
                                               vals['var_files'], False, {'title': name})
            client.create_blueprint(bp_json)
            click.secho('Created blueprint {0}'.format(name), fg='green')
        except BlueprintException:
            click.secho('Blueprint {0} NOT created\n'.format(name), fg='magenta')


def get_blueprint_id(client, blueprint_title):
    found_blueprints = client.search_blueprints(title=blueprint_title)

    if len(found_blueprints) == 0:
        raise click.Abort('Blueprint "{0}" does not exist'.format(blueprint_title))
    elif len(found_blueprints) > 1:
        raise click.Abort('Multiple blueprints matching "{0}" were found'.format(blueprint_title))
    else:
        return found_blueprints[0]['id']


@blueprints.command(name='delete')
@pass_client
@click.argument('title')
def delete_blueprint(client, title):
    """
    Delete a blueprint
    """
    blueprint_id = get_blueprint_id(client, title)

    click.confirm('Really delete blueprint {0}?'.format(title), abort=True)

    click.echo('Deleting {0}'.format(title))
    client.delete_blueprint(blueprint_id)


@blueprints.command(name='delete-all')
@pass_client
@click.confirmation_option('-y', '--yes', prompt='Really delete all blueprints?  This is '
                           'completely destructive, and you will never get them back.')
def delete_all_blueprints(client):
    """
    Delete all blueprints
    """
    for blueprint in client.list_blueprints():
        client.delete_blueprint(blueprint['id'])
        click.secho('Deleted blueprint {0}'.format(blueprint['title']), fg='magenta')


@blueprints.command(name='create-label')
@pass_client
@click.argument('title')
@click.argument('key')
@click.argument('value')
def create_label(client, title, key, value):
    """
    Create a key:value label on a blueprint
    """
    blueprint_id = get_blueprint_id(client, title)

    client.add_blueprint_label(blueprint_id, key, value)

    click.echo('Created label on {0}'.format(title))
