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

import sys
import time
from functools import update_wrapper

import click

from stackdio.client import StackdioClient


class TimeoutException(Exception):
    pass


# Create our decorator
pass_client = click.make_pass_decorator(StackdioClient)


def print_summary(title, components):
    num_components = len(components)

    if num_components != 1:
        title += 's'

    click.echo('## {0} {1}'.format(num_components, title))

    for item in components:
        click.echo('- Title: {0}'.format(
            item.get('title')))

        if 'description' in item:
            click.echo('  Description: {0}'.format(item['description']))

        if 'status' in item:
            click.echo('  Status: {0}'.format(item['status']))

        if 'status_detail' in item:
            click.echo('  Status Detail: {0}'.format(item['status_detail']))

        # Print a newline after each entry
        click.echo()


def poll_and_wait(func):
    """
    Execute func in increments of sleep_time for no more than max_time.
    Raise TimeoutException if we're not successful in max_time
    """
    def decorator(args=None, sleep_time=2, max_time=120):
        args = args or []

        current_time = 0

        click.echo('.', nl=False, file=sys.stderr)
        success = func(*args)
        while not success and current_time < max_time:
            current_time += sleep_time
            time.sleep(sleep_time)
            click.echo('.', nl=False, file=sys.stderr)
            success = func(*args)

        if not success:
            raise TimeoutException()

    return update_wrapper(decorator, func)
