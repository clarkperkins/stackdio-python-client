from __future__ import print_function

import sys
import os
import json

import click
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, meta
from jinja2.exceptions import TemplateNotFound, TemplateSyntaxError, UndefinedError
from jinja2.nodes import Assign, Block, Const, If, Not
from jinja2.filters import do_replace, evalcontextfilter


class BlueprintException(Exception):
    pass


class BlueprintGenerator(object):
    """
    Blueprint generator class.  Uses Jinja2 to generate blueprints from JSON
    templates, with inheritance.
    """

    def __init__(self, templates_path, output_stream=sys.stdout):
        """
        Need to create the jinja2 environment

        :param templates_path: A list of directories in which to look for templates
        :return:
        """
        self.settings = {
            'template_dir': os.path.expanduser('~/.stackdio-blueprints/templates')
        }

        self.sentinel = object()

        self.out_stream = output_stream

        templates_path.append(self.settings['template_dir'])

        self.env = Environment(
            loader=FileSystemLoader(templates_path),
            undefined=StrictUndefined)

        # Add a filter for json - then we can put lists, etc in our templates
        self.env.filters['json'] = lambda value: json.dumps(value)  # pylint: disable=unnecessary-lambda

        # Add a filter for newline escaping.  Essentially just a wrapper around the
        # replace('\n', '\\n') filter
        # Need the evalcontext filter decorator b/c do_replace uses it too and needs a ctx arg
        self.env.filters['longstring'] = evalcontextfilter(
            lambda ctx, s: do_replace(ctx, s, '\n', '\\n')
        )

    def error_exit(self, message, newlines=1):
        """
        Prints an error message in red and exits with an error code
        :param message: The error message
        :param newlines: the number of newlines to print at the end
        :return: None
        """
        click.secho(message, file=self.out_stream, nl=False, fg='red')
        click.echo('\n' * newlines, nl=False)
        raise BlueprintException()

    def warning(self, message, newlines=1):
        """
        Prints a warning message in brown
        :param message: The warning message to print
        :param newlines: The number of newlines to print at the end
        :return: None
        """
        click.secho(message, file=self.out_stream, nl=False, fg='yellow')
        click.echo('\n' * newlines, nl=False)

    def prompt(self, message):
        """
        Prompts the user for an input.  Prints the prompt to the configured output stream in green
        :param message: the prompt message
        :return: the value the user inputted
        """
        click.secho(message, file=self.out_stream, nl=False, fg='green')
        raw = sys.stdin.readline().strip()

        # This should work nicely - if yaml can't parse it properly, then it should be fine to just
        # return the raw string
        try:
            yaml_parsed = yaml.safe_load(raw)

            # safe_load returns None if the input is the empty string, so we want to put it back
            # to the empty string
            if yaml_parsed is None:
                return ''
            else:
                return yaml_parsed
        except Exception:
            # yaml couldn't parse it
            return raw

    def find_set_vars(self, ast):
        """
        We need this due to the fact that jinja DOES NOT allow you to override
        variables in base templates from derived templates.  This pulls out the
        assignments in derived templates so that we can set them in the context
        later.

        :param ast: the jinja2 parsed abstract syntax tree
        :return: the dict of all set variables
        :rtype: dict
        """
        ret = {}

        # TODO maybe use a set here.  I had originally used a dict because set tags in derived
        # templates would not get picked up by base templates.  The Jinja2 documentation even says
        # that this is the case.  So I was going to pick out the values from the set statements and
        # pass them in under the template context so they would get picked up by base templates.
        #
        # As soon as I took the time to write this whole function to do the above, I ran the
        # generator again, and my set statements in derived templates were getting picked up by the
        # base, and I have no clue why.  So none of the values in this dict are getting utilized,
        # just the keys.
        #
        # EDIT:  Turns out we do need the values.  When you do a template include, those values are
        # not allowed to be set by the template that did the include.

        for tag in ast.body:
            if isinstance(tag, Assign):
                if isinstance(tag.node, Const):
                    ret[tag.target.name] = tag.node.value
                else:
                    # This is OK - RHS is an expr instead of a constant.  Keep track of these so we
                    # don't get an error later
                    ret[tag.target.name] = self.sentinel

            elif isinstance(tag, If):
                # This is a simple naive check to see if we care about the variable being set.
                # Basically, if there is a variable inside an "if <var> is not undefined" block,
                # It is OK if that variable is not set in a derived template or var file since it
                # is an optional configuration value
                if isinstance(tag.test, Not) and tag.test.node.name == 'undefined':
                    ret[tag.test.node.node.name] = None

            elif isinstance(tag, Block):
                # Found a block, could be if statements within the block.  Recursive call
                # TODO: not sure if this will cause a bug, since set statements are local to blocks
                ret.update(self.find_set_vars(tag))

        return ret

    def validate(self, template_file):
        """
        Find all available and overridden vars in a template.  Recursively checks all
        super templates.

        :param template_file: The name of the template file
        :return: the set and unset variables
        :rtype: tuple
        """
        # Get all the info for the CURRENT template
        # Get the source of the template
        template_source = self.env.loader.get_source(self.env, template_file)[0]
        # parse it into an abstract syntax tree
        ast = self.env.parse(template_source)

        # the UNSET variables in the current template
        unset_vars = meta.find_undeclared_variables(ast)

        # the SET variables in the current template
        set_vars = self.find_set_vars(ast)

        # validate the super templates
        super_templates = meta.find_referenced_templates(ast)

        for template in super_templates:
            # Get all the information about the super template recursively
            super_unset, super_set = self.validate(template)

            # We do it this way so values in derived templates override those in base templates
            super_set.update(set_vars)
            set_vars = super_set

            unset_vars = unset_vars.union(super_unset)

        return unset_vars, set_vars

    def generate(self, template_file, var_files=(), variables=None, prompt=False, debug=False):
        """
        Generate the rendered blueprint and return it as a python dict

        The var_file is loaded first.  Anything in the variables dict *WILL OVERRIDE* the value in
        the var_vile.

        :param template_file: The relative location of the template.  It must be in one of the
        directories you specified when creating the Generator object.
        :param var_files: The location of the variable file(s) (relative or absolute)
        :param variables: A dict of variables to put in the template.
        :param prompt: Option to prompt for missing variables
        :param debug: Print the output of the template before trying to parse it as JSON
        :return: the generated blueprint object
        :rtype: dict
        """
        try:
            # Validate the template
            all_vars, set_vars = self.validate(template_file)

            context = {}
            for var_file in var_files:
                yaml_parsed = yaml.safe_load(var_file)
                if yaml_parsed:
                    context.update(yaml_parsed)

            # Add in the variables
            if variables:
                context.update(variables)

            # Find the null variables in the var file
            null_vars = set()

            for name, value in context.items():
                if value is None:
                    null_vars.add(name)
                    context[name] = ''

            # the missing vars should be the subset of all the variables
            # with the set of set variables and set of context variables taken
            # out
            missing_vars = all_vars - set(set_vars) - set(context)

            if missing_vars:
                if prompt:
                    # Prompt for missing vars
                    for var in sorted(missing_vars):
                        context[var] = self.prompt('{0}: '.format(var))
                else:
                    # Print an error
                    error_str = 'Missing variables:\n'
                    for var in sorted(missing_vars):
                        error_str += '   {0}\n'.format(var)
                    self.error_exit(error_str, 0)

            # Find the set of optional variables (ones inside of a 'if <var> is not undefined'
            # block).  They were set to None in the set_vars dict inside the validate method
            optional_vars = set()

            for var, val in set_vars.items():
                if val is None:
                    optional_vars.add(var)
                    # Need to get rid of this now so it doesn't cause problems later
                    del set_vars[var]
                elif val == self.sentinel:
                    # These are valid assignments, but we don't need to throw them in to the context
                    del set_vars[var]

            # If it is set elsewhere, it's not an issue
            optional_vars = optional_vars - set(context)

            if null_vars:
                warn_str = '\nWARNING: Null variables (replaced with empty string):\n'
                for var in null_vars:
                    warn_str += '   {0}\n'.format(var)
                self.warning(warn_str, 0)

            # Print a warning if there's unset optional variables
            if optional_vars:
                warn_str = '\nWARNING: Missing optional variables:\n'
                for var in sorted(optional_vars):
                    warn_str += '   {0}\n'.format(var)
                self.warning(warn_str, 0)

            # Generate the blueprint
            template = self.env.get_template(template_file)

            # Put the set vars into the context
            set_vars.update(context)
            context = set_vars

            template_json = template.render(**context)

            if debug:
                click.echo('\n')
                click.echo(template_json)
                click.echo('\n')

            # Return a dict object rather than a string
            return json.loads(template_json)

        except TemplateNotFound:
            self.error_exit('Your template file {0} was not found.'.format(template_file))
        except TemplateSyntaxError as e:
            self.error_exit('Invalid template error at line {0}:\n{1}'.format(
                e.lineno,
                str(e)
            ))
        except UndefinedError as e:
            self.error_exit('Missing variable: {0}'.format(str(e)))
        # except ValueError:
        #     self.error_exit('Invalid JSON.  Check your template file.')
