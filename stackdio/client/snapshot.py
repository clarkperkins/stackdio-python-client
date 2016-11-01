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


class SnapshotMixin(HttpMixin):

    @post('cloud/snapshots/')
    def create_snapshot(self, snapshot):
        """Create a snapshot"""
        return snapshot

    @get('cloud/snapshots/', paginate=True)
    def list_snapshots(self, **kwargs):
        pass

    @get('cloud/snapshots/{snapshot_id}/')
    def get_snapshot(self, snapshot_id):
        pass

    @delete('cloud/snapshots/{snapshot_id}/')
    def delete_snapshot(self, snapshot_id):
        pass
