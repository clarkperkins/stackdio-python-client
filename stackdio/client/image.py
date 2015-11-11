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


class ImageMixin(HttpMixin):

    @post('cloud/images/')
    def create_image(self, title, image_id, ssh_user, cloud_provider, default_instance_size=None):
        """Create a image"""
        return {
            "title": title,
            "image_id": image_id,
            "ssh_user": ssh_user,
            "cloud_provider": cloud_provider,
            "default_instance_size": default_instance_size
        }

    @get('cloud/images/', paginate=True)
    def list_images(self):
        """List all images"""
        pass

    @get('cloud/images/{image_id}/')
    def get_image(self, image_id):
        """Return the image that matches the given id"""
        pass

    @get('cloud/images/', paginate=True)
    def search_images(self, **kwargs):
        """List all images"""
        pass

    @delete('cloud/images/{image_id}/')
    def delete_image(self, image_id):
        """Delete the image with the given id"""
        pass
