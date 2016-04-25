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

from .exceptions import BlueprintException
from .http import HttpMixin, get, post, put, patch, delete


class BlueprintMixin(HttpMixin):

    @post('blueprints/')
    def create_blueprint(self, blueprint):
        """Create a blueprint"""

        if 'host_definitions' not in blueprint:
            raise BlueprintException('Blueprints must contain a list of host_definitions')

        formula_map = {}

        if 'formula_versions' in blueprint:
            all_formulas = self.list_formulas()

            used_formulas = []

            for formula_version in blueprint['formula_versions']:
                for formula in all_formulas:
                    if formula['uri'] == formula_version['formula']:
                        formula['version'] = formula_version['version']
                        used_formulas.append(formula)
                        break

            for formula in used_formulas:
                components = self.list_components_for_version(formula['id'], formula['version'])
                for component in components:
                    formula_map[component['sls_path']] = formula['uri']

        # check the provided blueprint to see if we need to look up any ids
        for host in blueprint['host_definitions']:
            for component in host.get('formula_components', []):
                if component['sls_path'] in formula_map:
                    component['formula'] = formula_map[component['sls_path']]

        return blueprint

    @get('blueprints/', paginate=True)
    def list_blueprints(self):
        pass

    @get('blueprints/{blueprint_id}/')
    def get_blueprint(self, blueprint_id):
        pass

    @get('blueprints/', paginate=True)
    def search_blueprints(self, **kwargs):
        pass

    @delete('blueprints/{blueprint_id}/')
    def delete_blueprint(self, blueprint_id):
        pass

    @put('blueprints/{blueprint_id}/properties/')
    def update_blueprint_properties(self, blueprint_id, properties):
        return properties

    @patch('blueprints/{blueprint_id}/properties/')
    def partial_update_blueprint_properties(self, blueprint_id, properties):
        return properties

    @post('blueprints/{blueprint_id}/labels/')
    def add_blueprint_label(self, blueprint_id, key, value):
        return {
            'key': key,
            'value': value,
        }

    @put('blueprints/{blueprint_id}/labels/{key}/')
    def update_blueprint_label(self, blueprint_id, key, value):
        return {
            'key': key,
            'value': value,
        }

    @delete('blueprints/{blueprint_id}/labels/{key}/')
    def delete_blueprint_label(self, blueprint_id, key):
        pass
