# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


def response(**kwargs):
    res = {}
    res['response'] = {k:v for k,v in kwargs.items()}
    res['success'] = True if not 'error' in res['response'].keys() else False
    
    return res

class Response(object):
    
    _error = ''
    _success = True
    _data = []
    _count = 0
    
    _fields = ['error', 'success', 'data', 'count']
    
    def __init__(self, **kwargs):
        pass
    
    @property
    def error(self):
        return self._error
    
    @error.setter
    def error(self, msg):
        self._error = msg
    
    @property
    def success(self):
        return True if not self._error else False
    
    @property
    def count(self):
        return len(self.data)
    
    def add(self, value, **kwargs):
        split = kwargs.get('split', False)
        if split:
            [self.data.append(x) for x in value]
        else:
            self.data.append(value)
    
    def _construct(self):
        return {k:v for k,v in zip(self._fields, self.__dict__.items())}
    
    def send(self):
        return self._construct()
        

class Record(object):
    
    _many2one = []
    _one2many = []
    _many2many = []
    
    _required = []
    _readonly = []
    _protected = ['create_date', 'write_date']
    
    _labels = {}
    
    def __init__(self, model, **kwargs):
        self._model = model
        self._name = self._model._name if self._model else ''
        if self._model:
            self.introspect()
        
    def __bool__(self):
        return bool(self._model)
    
    @property
    def fields(self):
        return self._model.fields_get_keys()
    
    def introspect(self):
        for field in self.fields:
            item = self._model.fields_get(field).get(field, {})
            for key,value in item.items():
                if '_'+key in self.__dict__:
                    self.__dict__['_'+key].append(field)
                self._labels[field] = item.get('string', False)
                
    def __repr__(self):
        return {
            'name': self._name, 
            'fields': self._labels, 
            'relationnal': {
                'many2one': self._many2one, 
                'one2many': self._one2many, 
                'many2many': self._many2many, 
            }
            'required': self._required, 
            'readonly': self._readonly, 
            'protected': self._protected, 
        }
        
        

class PingService(Component):
    _inherit = 'base.rest.service'
    _name = 'ping.service'
    _usage = 'ping'
    _collection = 'my_module.services'

    def _get_model_by_name(self, name):
        model = self.env.get(name, False)
        return Record(model)

    # The following method are 'public' and can be called from the controller.
    def get(self, _id, message):
        return {
            'response': 'Get called with message ' + message}

    def search(self, **kwargs):
        
        model = kwargs.get('model', False)
        response = Response(model=model)
        if not model:
            response.error = 'model is required'
            return response.send()
        
        model_id = self._get_model_by_name(model)
        try:
            results = model_id.search([])
            response.add(results.mapped('name'), split=True)
            
        except AttributeError:
            response.error = "unknown model '{}'".format(model)
        finally:
            return response.send()
        
        

        

    def update(self, _id, message):
        return {'response': 'PUT called with message ' + message}

    # pylint:disable=method-required-super
    def create(self, **params):
        return {'response': 'POST called with message ' + params['message']}

    def delete(self, _id):
        return {'response': 'DELETE called with id %s ' % _id}

    # Validator
    def _validator_search(self):
        return {'model': {'type': 'string'}}

    # Validator
    def _validator_get(self):
        # no parameters by default
        return {}

    def _validator_update(self):
        return {'message': {'type': 'string'}}

    def _validator_create(self):
        return {'message': {'type': 'string'}}