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


    def get_component_id(self, formula, component_title):
        """Get the id for a component from formula_id that matches title"""

        for component in formula.get("components"):
            if component.get("title") == component_title:
                return component.get("id")

        raise StackException("Component %s not found for formula %s" %
                             (component_title, formula.get("title")))
