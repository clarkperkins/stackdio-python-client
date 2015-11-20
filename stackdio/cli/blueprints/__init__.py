from __future__ import print_function

import argparse
import os
import json
import sys

from stackdio.cli.blueprints.generator import BlueprintException, BlueprintGenerator


def main():
    parser = argparse.ArgumentParser(
        description='invoke the stackdio blueprint generator')

    parser.add_argument('template_file',
                        help='The template file to generate from')

    parser.add_argument('var_files',
                        metavar='var_file',
                        nargs='*',
                        help='The variable files with your custom config.  They will be loaded '
                             'from left to right, so variables in the rightmost var files will '
                             'override those in var files to the left.')

    parser.add_argument('-p', '--prompt',
                        action='store_true',
                        help='Prompt user for missing variables')

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Print out json string before parsing the json')

    args = parser.parse_args()

    try:
        # Throw all output to stderr
        gen = BlueprintGenerator([os.path.curdir,
                                  os.path.join(os.path.curdir, 'templates'),
                                  os.path.dirname(os.path.abspath(args.template_file))],
                                 output_stream=sys.stderr)

        # Generate the blueprint
        blueprint = gen.generate(args.template_file,
                                 var_files=args.var_files,
                                 prompt=args.prompt,
                                 debug=args.debug)
    except BlueprintException:
        sys.exit(1)

    print(json.dumps(blueprint, indent=2))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write('Aborting...\n')
        sys.exit(1)
