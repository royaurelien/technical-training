# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.exceptions import ValidationError 

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
    
    _relational_types = ['many2one', 'one2many', 'many2many']
    _protected = ['create_date', 'write_date']
    _attributes = ['required', 'readonly', 'store']

    
    def __init__(self, model, **kwargs):
        self._model = model
        self._name = self._model._name if self._model else ''
        
    def __bool__(self):
        return bool(self._name)
    
    def __len__(self):
        return len(self._model)
    
    def filter_fields(self, **kwargs):
        fields = set(self.fields)
        
        # filters
        types = kwargs.get('types', [])
        attributes = kwargs.get('attributes', [])
        
        if types:
            res = set([field for field in self.fields if self.field_get_attr(field, 'type') in types])
            fields = set.intersection(fields, res)
        
        if attributes:
            for attr in attributes:
                res = set([field for field in self.fields if self.field_get_attr(field, attr)])
                fields = set.intersection(fields, res)
        
        return list(fields)
            
   
    
    @property
    def relationals(self):
        return self.filter_fields(types=self._relational_types)
    
    @property
    def one2many(self):
        return self.filter_fields(types=['one2many'])
    
    @property
    def many2many(self):
        return self.filter_fields(types=['many2many'])
    
    @property
    def many2one(self):
        return self.filter_fields(types=['many2one'])    
    
    @property
    def required(self):
        return self.filter_fields(attributes=['required'])    
    
    @property
    def readonly(self):
        return self.filter_fields(attributes=['readonly'])
    
    @property
    def related(self):
        return self.filter_fields(attributes=['related'])    
    
    @property
    def labels(self):
        return {k:v for k,v in zip(self.fields, [self.field_get_attr(field, 'string') for field in self.fields])}
    
    @property
    def fields(self):
        return self._model.fields_get_keys()
    
    def field_get(self, name, default={}):
        return self._model.fields_get(name).get(name, default)
    
    def field_get_attr(self, name, attr, default=False):
        return self.field_get(name).get(attr, default)     

    @property
    def defaults(self):
        return self._model.default_get(self.fields)
                
    def __repr__(self):
        vals = {
            'name': self._name, 
            'fields': self.labels, 
            'relationnal': {
                'many2one': self.many2one, 
                'one2many': self.one2many, 
                'many2many': self.many2many, 
            }, 
            'required': self.required, 
            'readonly': self.readonly, 
#             'protected': self.protected, 
        }
        return "{}".format(vals)
    
    def get_create_schema(self):
        fields = list(set(self.required) - set(self.defaults))
        return {k:v for k,v in zip(fields, [self.field_get_attr(field, 'type') for field in self.fields])}
        
    def create(self, vals):
        defaults = self.defaults
        defaults.update(vals)
        
        # remove readonly fields if presents
        defaults = dict((k,v) for k,v in defaults.items() if k not in self.readonly)
        
        missing_fields = [field for field in self.required if field not in defaults.keys()]
        if missing_fields:
            raise ValidationError("Required field(s) missing: {}: ".format(missing_fields))
        
        return self._model.create(defaults)
        

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