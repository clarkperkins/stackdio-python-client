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


class AccountMixin(HttpMixin):

    @get('cloud/providers/', paginate=True)
    def list_providers(self):
        """List all providers"""
        pass

    @get('cloud/providers/', paginate=True)
    def search_providers(self, **kwargs):
        """Search for a provider"""
        pass

    @post('cloud/accounts/')
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

        return form_data

    @get('cloud/accounts/', paginate=True)
    def list_accounts(self):
        """List all account"""
        pass

    @get('cloud/accounts/{account_id}/')
    def get_account(self, account_id):
        """Return the account that matches the given id"""
        pass

    @get('cloud/accounts/')
    def search_accounts(self, **kwargs):
        """List all accounts"""
        pass

    @delete('cloud/accounts/{account_id}/')
    def delete_account(self, account_id):
        """List all accounts"""
        pass
