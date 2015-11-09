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


class FormulaMixin(HttpMixin):
    @endpoint("formulas/")
    def import_formula(self, formula_uri, public=True):
        """Import a formula"""
        data = {
            "uri": formula_uri,
            "public": public,
        }
        return self._post(endpoint, data=json.dumps(data), jsonify=True)

    @endpoint("formulas/")
    def list_formulas(self):
        """Return all formulas"""
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("formulas/{formula_id}/")
    def get_formula(self, formula_id, none_on_404=False):
        """Get a formula with matching id"""
        return self._get(endpoint, jsonify=True, none_on_404=none_on_404)

    @endpoint("formulas/")
    def search_formulas(self, **kwargs):
        """Get a formula with matching id"""
        return self._get(endpoint, params=kwargs, jsonify=True)['results']

    @endpoint("formulas/{formula_id}/")
    def delete_formula(self, formula_id):
        """Delete formula with matching id"""
        return self._delete(endpoint, jsonify=True)

    @endpoint("formulas/{formula_id}/action/")
    def update_formula(self, formula_id):
        """Delete formula with matching id"""
        return self._post(endpoint, json.dumps({"action": "update"}), jsonify=True)
