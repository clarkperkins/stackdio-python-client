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

from .http import HttpMixin, endpoint


class RegionMixin(HttpMixin):
    @endpoint("cloud/providers/{provider_name}/regions/")
    def list_regions(self, provider_name):
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("cloud/providers/{provider_name}/regions/{region_id}")
    def get_region(self, provider_name, region_id, none_on_404=False):
        return self._get(endpoint, jsonify=True, none_on_404=none_on_404)

    @endpoint("cloud/providers/{provider_name}/regions/")
    def search_regions(self, provider_name, **kwargs):
        return self._get(endpoint, params=kwargs, jsonify=True)['results']

    @endpoint("cloud/providers/{provider_name}/zones/")
    def list_zones(self):
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("cloud/providers/{provider_name}/zones/{zone_id}")
    def get_zone(self, provider_name, zone_id, none_on_404=False):
        return self._get(endpoint, jsonify=True, none_on_404=none_on_404)

    @endpoint("cloud/providers/{provider_name}/zones/")
    def search_zones(self, provider_name, **kwargs):
        return self._get(endpoint, params=kwargs, jsonify=True)['results']
