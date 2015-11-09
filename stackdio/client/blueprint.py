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

import json

from .http import HttpMixin, endpoint


class BlueprintMixin(HttpMixin):

    @endpoint("blueprints/")
    def create_blueprint(self, blueprint, provider="ec2"):
        """Create a blueprint"""

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
                components = self._get(
                    '{0}?version={1}'.format(formula['components'], formula['version']),
                    jsonify=True,
                )['results']
                for component in components:
                    formula_map[component['sls_path']] = formula['uri']

        # check the provided blueprint to see if we need to look up any ids
        for host in blueprint['host_definitions']:
            for component in host['formula_components']:
                if component['sls_path'] in formula_map:
                    component['formula'] = formula_map[component['sls_path']]

        return self._post(endpoint, data=json.dumps(blueprint), jsonify=True, raise_for_status=False)

    @endpoint("blueprints/")
    def list_blueprints(self):
        """Return info for a specific blueprint_id"""
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("blueprints/{blueprint_id}/")
    def get_blueprint(self, blueprint_id, none_on_404=False):
        """Return info for a specific blueprint_id"""
        return self._get(endpoint, jsonify=True, none_on_404=none_on_404)

    @endpoint("blueprints/")
    def search_blueprints(self, **kwargs):
        """Return info for a specific blueprint_id"""
        return self._get(endpoint, params=kwargs, jsonify=True)['results']

    @endpoint("blueprints/{blueprint_id}")
    def delete_blueprint(self, blueprint_id):
        return self._delete(endpoint, jsonify=True)
