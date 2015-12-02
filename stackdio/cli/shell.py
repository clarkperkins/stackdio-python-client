# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
from cmd import Cmd

import click

from stackdio.client.version import __version__


try:
    import readline
except ImportError:
    readline = None


HIST_FILE = os.path.join(os.path.expanduser('~'), '.stackdio-cli', 'history')


def get_invoke(ctx, command):
    def invoke(self, arg):
        return ctx.invoke(command)
    return invoke


def get_help(command):
    def help(self):
        click.echo(command.help)
    return help


def get_shell(ctx):

    # Make it a new-style class so we can use super
    class StackdioShell(Cmd, object):

        def __init__(self):
            super(StackdioShell, self).__init__()
            self.old_completer = None

        def preloop(self):
            # read our history
            if readline:
                try:
                    readline.read_history_file(HIST_FILE)
                except IOError:
                    pass

        def postloop(self):
            # Write our history
            if readline:
                readline.write_history_file(HIST_FILE)

        prompt = 'stackdio > '
        intro = 'stackdio shell v{0}'.format(__version__)

        # We need to override this to fix readline
        def cmdloop(self, intro=None):
            self.preloop()
            if self.use_rawinput and self.completekey and readline:
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                if 'libedit' in readline.__doc__:
                    # For mac
                    readline.parse_and_bind('bind ^I rl_complete')
                else:
                    # for other platforms
                    readline.parse_and_bind(self.completekey + ': complete')
            try:
                if intro is not None:
                    self.intro = intro
                if self.intro:
                    self.stdout.write(str(self.intro)+"\n")
                stop = None
                while not stop:
                    if self.cmdqueue:
                        line = self.cmdqueue.pop(0)
                    else:
                        if self.use_rawinput:
                            try:
                                line = raw_input(self.prompt)
                            except EOFError:
                                # We just want to quit here
                                self.stdout.write('\n')
                                break
                        else:
                            self.stdout.write(self.prompt)
                            self.stdout.flush()
                            line = self.stdin.readline()
                            if not len(line):
                                line = 'EOF'
                            else:
                                line = line.rstrip('\r\n')
                    line = self.precmd(line)
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)

            finally:
                self.postloop()
                if self.use_rawinput and self.completekey and readline:
                    readline.set_completer(self.old_completer)

        def emptyline(self):
            pass

        def do_quit(self, arg):
            return True

        def do_exit(self, arg):
            return True

    for name, command in ctx.command.commands.items():
        setattr(StackdioShell, 'do_%s' % name.replace('-', '_'), get_invoke(ctx, command))

        if command.help is not None:
            setattr(StackdioShell, 'help_%s' % name.replace('-', '_'), get_help(command))

    return StackdioShell()
