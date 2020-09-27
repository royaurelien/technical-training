# -*- coding: utf-8 -*-

from odoo import models, fields, api


class IrModel(models.Model):
    _inherit = 'ir.model'
    
    expose = fields.Boolean(string='Expose on API', default=False)
    
    
class Base(models.AbstractModel):
    _inherit = 'base'
    
    _relational_types = ['many2one', 'one2many', 'many2many']
    _protected = ['create_date', 'write_date']
    _attributes = ['required', 'readonly', 'store']
    
    def _filter_fields(self, **kwargs):
        fields = set(self._fields_list)
        
        # filters
        types = kwargs.get('types', [])
        attributes = kwargs.get('attributes', [])
        
        if types:
            res = set([field for field in self._fields_list if self.field_get_attr(field, 'type') in types])
            fields = set.intersection(fields, res)
        
        if attributes:
            for attr in attributes:
                res = set([field for field in self._fields_list if self.field_get_attr(field, attr)])
                fields = set.intersection(fields, res)
        
        return list(fields)
            
   
    
    @property
    def _relationals(self):
        return self._filter_fields(types=self._relational_types)

    @property
    def _binary(self):
        return self._filter_fields(types=['binary'])    
    
    @property
    def _one2many(self):
        return self._filter_fields(types=['one2many'])
    
    @property
    def _many2many(self):
        return self._filter_fields(types=['many2many'])
    
    @property
    def _many2one(self):
        return self._filter_fields(types=['many2one'])    
    
    @property
    def _required(self):
        return self._filter_fields(attributes=['required'])    
    
    @property
    def _readonly(self):
        return self._filter_fields(attributes=['readonly'])
    
    @property
    def _related(self):
        return self._filter_fields(attributes=['related'])    
    
    @property
    def _labels(self):
        return {k:v for k,v in zip(self._fields_list, [self.field_get_attr(field, 'string') for field in self._fields_list])}
    
    @property
    def _fields_list(self):
        return self.fields_get_keys()
    
    def field_get(self, name, default={}):
        return self.fields_get(name).get(name, default)
    
    def field_get_attr(self, name, attr, default=False):
        return self.field_get(name).get(attr, default)     

    @property
    def _defaults(self):
        return self.default_get(self._fields_list)

    def get_create_schema(self, **kwargs):
        void = kwargs.get('void', False)
        fields = list(set(self._required) - set(self._defaults))
        return {k:v for k,v in zip(fields, [self.field_get_attr(field, 'type') for field in self._fields_list])}
        
    def get_schema(self, **kwargs):
        void = kwargs.get('void', False)
        fields = self._fields_list
        return {k:v for k,v in zip(fields, [self.field_get_attr(field, 'type') for field in fields])}        
        
    def external_create(self, vals, **kwargs):
        skip_required = kwargs.get('ignore', True)
        logging = kwargs.get('logging', True)
        
        defaults = self._defaults
        defaults.update(vals)
        
        # remove readonly fields if presents
        defaults = dict((k,v) for k,v in defaults.items() if k not in self._readonly)
        
        missing_fields = [field for field in self._required if field not in defaults.keys()]
        if missing_fields and not skip_required:
            raise ValidationError("Required field(s) missing: {}: ".format(missing_fields))
        
        return self.create(defaults)    