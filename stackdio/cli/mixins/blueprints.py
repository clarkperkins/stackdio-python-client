from __future__ import print_function

import json
import os
import argparse
import sys

import yaml
from cmd2 import Cmd

from stackdio.client.exceptions import StackException
from stackdio.cli.blueprints.generator import BlueprintGenerator, BlueprintException


class BlueprintNotFound(Exception):
    pass


class BlueprintMixin(Cmd):
    BLUEPRINT_COMMANDS = ["list", "list-templates", "create", "create-all", "delete", "delete-all"]

    def do_blueprints(self, arg):
        """Entry point to controlling blueprints."""

        USAGE = "Usage: blueprints COMMAND\nWhere COMMAND is one of: %s" % (
            ", ".join(self.BLUEPRINT_COMMANDS))

        args = arg.split()
        if not args or args[0] not in self.BLUEPRINT_COMMANDS:
            print(USAGE)
            return

        bp_cmd = args[0]

        # Sneakiness for argparse
        saved = sys.argv[0]
        sys.argv[0] = 'blueprints {0}'.format(bp_cmd)

        if bp_cmd == "list":
            self._list_blueprints()
        elif bp_cmd == "list-templates":
            self._list_templates()
        elif bp_cmd == "create":
            self._create_blueprint(args[1:])
        elif bp_cmd == "create-all":
            self._create_all(args[1:])
        elif bp_cmd == "delete":
            self._delete_blueprint(args[1:])
        elif bp_cmd == "delete-all":
            self._delete_all()

        else:
            print(USAGE)

        # End sneakiness
        sys.argv[0] = saved

    def complete_blueprints(self, text, line, begidx, endidx):
        # not using line, begidx, or endidx, thus the following pylint disable
        # pylint: disable=W0613
        return [i for i in self.BLUEPRINT_COMMANDS if i.startswith(text)]

    def help_blueprints(self):
        print("Manage blueprints.")
        print("Sub-commands can be one of:\n\t{0}".format(
            ", ".join(self.BLUEPRINT_COMMANDS)))
        print("Try 'blueprints COMMAND' to get help on (most) sub-commands")

    def _list_blueprints(self):
        """List all blueprints"""

        print("Getting blueprints ... ")
        blueprints = self.stacks.list_blueprints()
        self._print_summary("Blueprint", blueprints)

    def _recurse_dir(self, dirname, extensions, prefix=''):
        for template in os.listdir(dirname):
            if os.path.isdir(os.path.join(dirname, template)):
                # Recursively look at the subdirectories
                self._recurse_dir(os.path.join(dirname, template),
                                  extensions,
                                  prefix + template + os.sep)
            elif template.split('.')[-1] in extensions and not template.startswith('_'):
                print('    {0}'.format(prefix + template))

    def _list_templates(self):
        if 'blueprint_dir' not in self.config:
            print("Missing blueprint directory config")
            return

        blueprint_dir = os.path.expanduser(self.config['blueprint_dir'])

        print('Template mappings:')
        mapping = yaml.safe_load(open(os.path.join(blueprint_dir, 'mappings.yaml'), 'r'))
        if mapping:
            for blueprint in mapping:
                print('    {0}'.format(blueprint))

        print('')

        print('Templates:')
        self._recurse_dir(os.path.join(blueprint_dir, 'templates'), ['json'])

        print('')

        print('Var files:')
        self._recurse_dir(os.path.join(blueprint_dir, 'var_files'), ['yaml', 'yml'])

    def _create_blueprint(self, args, bootstrap=False):
        """Create a blueprint"""

        parser = argparse.ArgumentParser()

        parser.add_argument('-m', '--mapping',
                            help='The entry in the map file to use')

        parser.add_argument('-t', '--template',
                            help='The template file to use')

        parser.add_argument('-v', '--var-file',
                            action='append',
                            help='The variable files to use.  You may pass in more than one.  They '
                                 'will be loaded from left to right, so variables in the rightmost '
                                 'var files will override those in var files to the left.')

        parser.add_argument('-n', '--no-prompt',
                            action='store_false',
                            help='Don\'t prompt for missing variables in the template')

        args = parser.parse_args(args)

        if not bootstrap:
            print(self.colorize(
                "Advanced users only - use the web UI if this isn't you!\n",
                "green"))

            if not args.template and not args.mapping:
                print(self.colorize('You must specify either a template or a mapping\n', 'red'))
                parser.print_help()
                return

        blueprint_dir = os.path.expanduser(self.config['blueprint_dir'])

        template_file = args.template
        # Should always be a list, and the generator can handle that
        var_files = args.var_file
        if not var_files:
            # If -v is never specified, argparse give back None, we need a list
            var_files = []

        if args.mapping:
            mapping = yaml.safe_load(open(os.path.join(blueprint_dir, 'mappings.yaml'), 'r'))
            if not mapping or args.mapping not in mapping:
                print(self.colorize('You gave an invalid mapping.', 'red'))
                return
            else:
                template_file = mapping[args.mapping].get('template')
                var_files = mapping[args.mapping].get('var_files', [])
                if not template_file:
                    print(self.colorize('Your mapping must specify a template.', 'red'))
                    return

        bp_json = self._create_single(template_file, var_files, args.no_prompt)

        if not bp_json:
            # There was an error with the blueprint creation, and there should already be an
            # error message printed
            return

        if not bootstrap:
            print("Creating blueprint")

        r = self.stacks.create_blueprint(bp_json, raise_for_status=False)
        print(json.dumps(r, indent=2))

    def _create_single(self, template_file, var_files, no_prompt):
        blueprint_dir = os.path.expanduser(self.config['blueprint_dir'])

        gen = BlueprintGenerator([os.path.join(blueprint_dir, 'templates')])

        if not os.path.exists(os.path.join(blueprint_dir, 'templates', template_file)):
            print(self.colorize('You gave an invalid template', 'red'))
            return

        if template_file.startswith('_'):
            print(self.colorize("WARNING: Templates beginning with '_' are generally not meant to "
                                "be used directly.  Please be sure this is really what you want.\n",
                                "magenta"))

        final_var_files = []

        # Build a list with full paths in it instead of relative paths
        for var_file in var_files:
            var_file = os.path.join(blueprint_dir, 'var_files', var_file)
            if os.path.exists(var_file):
                final_var_files.append(var_file)
            else:
                print(self.colorize("WARNING: Variable file {0} was not found.  "
                                    "Ignoring.".format(var_file), "magenta"))

        # Generate the JSON for the blueprint
        return gen.generate(template_file,
                            final_var_files,  # Pass in a list
                            prompt=no_prompt)

    def _create_all(self, args):
        """Create all the blueprints in the map file"""
        parser = argparse.ArgumentParser()

        parser.add_argument('--no-prompt',
                            action='store_false',
                            help='Don\'t prompt to create all blueprints')

        args = parser.parse_args(args)

        if args.no_prompt:
            really = raw_input("Really create all blueprints (y/n)? ")
            if really not in ['Y', 'y']:
                return

        blueprint_dir = os.path.expanduser(self.config['blueprint_dir'])
        mapping = yaml.safe_load(open(os.path.join(blueprint_dir, 'mappings.yaml'), 'r'))

        for name, vals in mapping.items():
            try:
                bp_json = self._create_single(vals['template'], vals['var_file'], False)
                self.stacks.create_blueprint(bp_json)
                print(self.colorize('Created blueprint {0}'.format(name), 'green'))
            except BlueprintException:
                print(self.colorize('Blueprint {0} NOT created\n'.format(name), 'magenta'))

    def _delete_blueprint(self, args):
        """Delete a blueprint"""

        if len(args) != 1:
            print("Usage: blueprint delete BLUEPRINT_NAME")
            return

        blueprint_id = self._get_blueprint_id(args[0])

        really = raw_input("Really delete blueprint {0} (y/n)? ".format(args[0]))
        if really not in ["y", "Y"]:
            print("Aborting deletion")
            return

        print("Deleting {0}".format(args[0]))
        self.stacks.delete_blueprint(blueprint_id)
        self._list_blueprints()

    def _delete_all(self):
        """Delete all blueprints"""
        really = raw_input("Really delete all blueprints?  This is completely destructive, and you "
                           "will never get them back. (y/n) ")
        if really not in ['Y', 'y']:
            return

        for blueprint in self.stacks.list_blueprints():
            self.stacks.delete_blueprint(blueprint['id'])
            print(self.colorize('Deleted blueprint {0}'.format(blueprint['title']), 'magenta'))

    def _get_blueprint_id(self, blueprint_name):
        """Validate that a blueprint exists"""

        try:
            return self.stacks.get_blueprint_id(blueprint_name)
        except StackException:
            print(self.colorize(
                "Blueprint [{0}] does not exist".format(blueprint_name),
                "red"))
            raise
