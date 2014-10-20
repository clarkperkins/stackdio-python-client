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

from .exceptions import StackException
from .http import HttpMixin, endpoint
from .version import accepted_versions, deprecated


class RegionMixin(HttpMixin):


    @accepted_versions(">=0.6.1")
    @endpoint("regions/")
    def list_regions(self):
        return self._get(endpoint, jsonify=True)['results']


    @accepted_versions(">=0.6.1")
    @endpoint("regions/")
    def search_regions(self, **kwargs):
        return self._get(endpoint, params=kwargs, jsonify=True)['results']


    @deprecated
    @accepted_versions(">=0.6", "<0.7")
    @endpoint("regions/")
    def get_region_id(self, title, type_name="ec2"):
        """Get a zone id for title"""

        provider_type = self.get_provider_type(type_name)
        params = {
            "title": title,
            "provider_type": provider_type["id"]
        }
        result = self._get(endpoint, params=params, jsonify=True)
        if len(result['results']) == 1:
            return result['results'][0]['id']

        raise StackException("Zone %s not found for %s" % (title, type_name))


    @accepted_versions("!=0.6")
    @endpoint("zones/")
    def list_zones(self):
        return self._get(endpoint, jsonify=True)['results']


    @accepted_versions(">=0.6.1")
    @endpoint("zones/")
    def search_zones(self, **kwargs):
        return self._get(endpoint, params=kwargs, jsonify=True)['results']


    @deprecated
    @accepted_versions("!=0.6", "<0.7")
    @endpoint("zones/")
    def get_zone_id(self, title, type_name="ec2"):
        """Get a zone id for title"""

        result = self._get(endpoint, jsonify=True)
        for zone in result['results']:
            if zone.get("title") == title and \
               zone.get("provider_type") == type_name:
                return zone.get("id")

        raise StackException("Zone %s not found for %s" % (title, type_name))
