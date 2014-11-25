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

from .exceptions import StackException
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
    def get_formula(self, formula_id):
        """Get a formula with matching id"""
        return self._get(endpoint, jsonify=True)

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

    def get_formula_id(self, title):
        """Find a stack id"""

        formulas = self.list_formulas()
        for formula in formulas:
            if formula.get("title") == title:
                return formula.get("id")

        raise StackException("Formula %s not found" % title)

    def get_component_id(self, formula, component_title):
        """Get the id for a component from formula_id that matches title"""

        for component in formula.get("components"):
            if component.get("title") == component_title:
                return component.get("id")

        raise StackException("Component %s not found for formula %s" %
                             (component_title, formula.get("title")))
