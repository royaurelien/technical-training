# -*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError


from ..tools import make_response, eval_request_params, load_model, extract_arguments

_logger = logging.getLogger(__name__)

VERSION = 1

class RestApi(http.Controller):
    
    @property
    def env(self):
        return http.request.env
    
    @http.route('/api/ping', methods=['GET'], auth='none', csrf=False)
    @make_response()
    def ping(self, **kw):
        return 'pong'

    
    @http.route('/api/auth', auth='none', methods=["POST"], csrf=False)
    @make_response()
    def authenticate(self, db, login, password):
        # Before calling /api/auth, call /web?db=*** otherwise web service is not found
        http.request.session.authenticate(db, login, password)
        return http.request.env['ir.http'].session_info()    
    
    
    @http.route([
        '/api/models', 
        '/api/models/<string:name>', 
        '/api/models/<string:name>/<string:item>', 
        '/api/models/<string:name>/<int:id>', 
    ], methods=['GET'], auth='user', csrf=False)
    @make_response()
    @load_model()
    def models_get(self, name=None, item=None, id=None, model=None, **kwargs):
        env = self.env
        
        if not name:
            domain = [('expose', '=', True)]
            domain = expression.AND([domain, ['&', ('transient','=',False), ('state', '=', 'base')]])

            ir_model = env['ir.model'].sudo().search(domain)
            models = ir_model.mapped('model')

            for model in models:
                if not env[model].with_user(env.user).check_access_rights('read', False):
                    models.remove(model)
            
            return models
        
        if name and item is None:
            return model.get_schema()
        
        if name and item:
            if not item in ['fields', 'methods', 'schema']:
                raise ValidationError("Method '{}' is not supported.".format(item))
            if item is "methods":
                pass
            if item is "schema":
                pass
            if item is "fields":
                return model._labels
            
            return model.get_schema()
        return {}
    
    
    @http.route([
        '/api/model/<string:name>', 
        '/api/model/<string:name>/<int:id>', 
    ], methods=['GET'], auth='user', csrf=False)
    @make_response()
    @load_model()
    def model_get(self, name, id=None, model=None, **kwargs):
        default_fields = list(set(model._fields_list) - set(model._binary) - set(model._one2many))
        
#         filters = extract_arguments(**kwargs)
        filters = eval_request_params(**kwargs)
        filters['fields'] = filters['fields'] if filters['fields'] else default_fields
        
        _logger.warning("{}".format(filters))
        
        if id:
            del filters['domain']
            return model.browse(id).read(**filters)
        
        return model.search_read(**filters)
    
    
    @http.route([
        '/api/model/<string:name>', 
        '/api/model/<string:name>/<int:id>', 
    ], methods=['POST'], auth='user', csrf=False)
    @make_response()
    @load_model()
    def model_post(self, name, id=None, model=None, **kwargs):
        vals = {}
        # UPDATE
        if id:
            res = model.browse(id).update(vals)
        else:
            res = model.external_create(vals)
        
        return res