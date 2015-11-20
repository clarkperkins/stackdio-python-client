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

from .http import HttpMixin, get, post, delete


class FormulaMixin(HttpMixin):
    @post('formulas/')
    def import_formula(self, formula_uri, git_username=None, git_password=None, access_token=None):
        """Import a formula"""
        data = {
            'uri': formula_uri,
        }

        if git_username:
            data['git_username'] = git_username
            data['git_password'] = git_password
            data['access_token'] = False
        elif access_token:
            data['git_username'] = access_token
            data['access_token'] = True

        return data

    @get('formulas/', paginate=True)
    def list_formulas(self):
        """Return all formulas"""
        pass

    @get('formulas/{formula_id}/')
    def get_formula(self, formula_id):
        """Get a formula with matching id"""
        pass

    @get('formulas/{formula_id}/components/?version={version}', paginate=True)
    def list_components_for_version(self, formula_id, version):
        pass

    @get('formulas/', paginate=True)
    def search_formulas(self, **kwargs):
        """Get a formula with matching id"""
        pass

    @delete('formulas/{formula_id}/')
    def delete_formula(self, formula_id):
        """Delete formula with matching id"""
        pass

    @post('formulas/{formula_id}/action/')
    def update_formula(self, formula_id):
        """Update the formula"""
        return {"action": "update"}
