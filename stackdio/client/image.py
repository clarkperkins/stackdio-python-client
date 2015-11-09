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


class ImageMixin(HttpMixin):

    @endpoint("cloud/images/")
    def create_image(self, title, image_id, ssh_user, cloud_provider,
                       default_instance_size=None):
        """Create a image"""
        data = {
            "title": title,
            "image_id": image_id,
            "ssh_user": ssh_user,
            "cloud_provider": cloud_provider,
            "default_instance_size": default_instance_size
        }
        return self._post(endpoint, data=json.dumps(data), jsonify=True)

    @endpoint("cloud/images/")
    def list_images(self):
        """List all images"""
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("cloud/images/{image_id}/")
    def get_image(self, image_id, none_on_404=False):
        """Return the image that matches the given id"""
        return self._get(endpoint, jsonify=True, none_on_404=none_on_404)

    @endpoint("cloud/images/")
    def search_images(self, image_id):
        """List all images"""
        return self._get(endpoint, jsonify=True)['results']

    @endpoint("cloud/images/{image_id}/")
    def delete_image(self, image_id):
        """Delete the image with the given id"""
        return self._delete(endpoint, jsonify=True)['results']
