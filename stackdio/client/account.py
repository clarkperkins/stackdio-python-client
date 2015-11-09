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


class AccountMixin(HttpMixin):

    @endpoint("cloud/providers/")
    def list_providers(self):
        """List all providers"""
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("cloud/providers/")
    def search_providers(self, provider_id):
        """List all providers"""
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("cloud/accounts/")
    def create_account(self, **kwargs):
        """Create an account"""

        form_data = {
            "title": None,
            "account_id": None,
            "provider": None,
            "access_key_id": None,
            "secret_access_key": None,
            "keypair": None,
            "security_groups": None,
            "route53_domain": None,
            "default_availability_zone": None,
            "private_key": None
        }

        for key in form_data.keys():
            form_data[key] = kwargs.get(key)

        return self._post(endpoint, data=json.dumps(form_data), jsonify=True)

    @endpoint("accounts/")
    def list_accounts(self):
        """List all account"""
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("accounts/{account_id}/")
    def get_account(self, account_id, none_on_404=False):
        """Return the account that matches the given id"""
        return self._get(endpoint, jsonify=True, none_on_404=none_on_404)

    @endpoint("accounts/")
    def search_accounts(self, account_id):
        """List all accounts"""
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("accounts/{account_id}/")
    def delete_account(self, account_id):
        """List all accounts"""
        return self._delete(endpoint, jsonify=True)['results']
