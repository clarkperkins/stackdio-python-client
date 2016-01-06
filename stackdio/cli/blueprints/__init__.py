from __future__ import print_function

import os
import json
import sys

import click

from stackdio.cli.blueprints.generator import BlueprintException, BlueprintGenerator


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('template_file')
@click.argument('var_files', nargs=-1, type=click.File('r'))
@click.option('-p', '--prompt', is_flag=True, default=False,
              help='Prompt user for missing variables')
@click.option('-d', '--debug', is_flag=True, default=False,
              help='Print out json string before parsing the json')
def main(template_file, var_files, prompt, debug):

    try:
        # Throw all output to stderr
        gen = BlueprintGenerator([os.path.curdir,
                                  os.path.join(os.path.curdir, 'templates'),
                                  os.path.dirname(os.path.abspath(template_file))],
                                 output_stream=sys.stderr)

        # Generate the blueprint
        blueprint = gen.generate(template_file,
                                 var_files=var_files,
                                 prompt=prompt,
                                 debug=debug)
    except BlueprintException:
        raise click.Abort('Error processing blueprint')

    click.echo(json.dumps(blueprint, indent=2))


if __name__ == '__main__':
    main()
