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
from .http import HttpMixin, endpoint, use_admin_auth
from .version import accepted_versions, deprecated


class ProfileMixin(HttpMixin):

    @use_admin_auth
    @endpoint("profile/")
    def create_profile(self, title, image_id, ssh_user, cloud_provider,
                       default_instance_size=None):
        """Create a profile"""
        data = {
            "title": title,
            "image_id": image_id,
            "ssh_user": ssh_user,
            "cloud_provider": cloud_provider,
            "default_instance_size": default_instance_size
        }
        return self._post(endpoint, data=json.dumps(data), jsonify=True)


    @endpoint("profiles/")
    def list_profiles(self):
        """List all profiles"""
        return self._get(endpoint, jsonify=True)['results']


    @endpoint("profiles/{profile_id}/")
    def get_profile(self, profile_id, none_on_404=False):
        """Return the profile that matches the given id"""
        return self._get(endpoint, jsonify=True, none_on_404=none_on_404)


    @accepted_versions(">=0.6.1")
    @endpoint("profiles/")
    def search_profiles(self, profile_id):
        """List all profiles"""
        return self._get(endpoint, jsonify=True)['results']


    @endpoint("profiles/{profile_id}/")
    def delete_profile(self, profile_id):
        """Delete the profile with the given id"""
        return self._delete(endpoint, jsonify=True)['results']


    @deprecated
    @accepted_versions("<0.7")
    def get_profile_id(self, slug, title=False):
        """Get the id for a profile that matches slug. If title is True will look
        at title instead."""

        profiles = self.list_profiles()
        for profile in profiles:
            if profile.get("slug" if not title else "title") == slug:
                return profile.get("id")

        return StackException("Profile %s not found" % slug)
