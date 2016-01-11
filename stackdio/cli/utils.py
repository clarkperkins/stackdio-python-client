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

import click


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
