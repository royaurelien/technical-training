import ast
import datetime
import inspect
from functools import wraps
import json
import logging

from odoo.http import request
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=E0202,arguments-differ
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)

#     def make_json_response(self, data, headers=None, cookies=None):
#         data = JSONEncoder().encode(data)
#         if headers is None:
#             headers = {}
#         headers["Content-Type"] = "application/json"
#         return self.make_response(data, headers=headers, cookies=cookies)

class make_response():
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            response = {
                'name_method': func.__name__, 
                'http_method': '', 
                'args': str(kwargs), 
                'success': True, 
                'message': '', 
                'results': {
                    'data': [], 
                    'count': 0,
                },
                'user': request.env.user.name,
            }            
            
            try:
                
                response['results']['data'] = decode_bytes(func(*args, **kwargs))
                response['results']['count'] = len(response['results']['data'])
                

            except Exception as e:
                response.update({
                    'message': str(e), 
                    'success': False, 
                })
            finally:
                response = JSONEncoder().encode(response)
                
                headers = {}                
                headers["Content-Type"] = "application/json"
                return request.make_response(response, headers=headers)
#                 return request.make_response(json.dumps(response))
            
        return wrapper
    
    
class load_model():
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            env = request.env
            user = env.user
            name = kwargs.get('name', False)
            sign = inspect.signature(func)
            required = True if sign.parameters.get('name').default is not None else False
            error = True if required and not name else False
            
            
            assert (not error), "name must be specified"
            
            if name:
                try:
                    model = env[name]
                    if not model.with_user(user).check_access_rights('read', False):
                        raise UserError("User {} doesn't have rights to access to {}.".format(user.name, name))
                        
                    kwargs['model'] = model
#                     return func(*args, **kwargs)
                except KeyError:
                    raise ValidationError("Model '{}' doesn't exist.".format(name))

            return func(*args, **kwargs)
        return wrapper    
    
    
def eval_request_params(**kwargs):
    items = ['domain', 'fields', 'groupby']
    for k, v in kwargs.items():
        try:
            kwargs[k] = safe_eval(v)
        except:
            continue

    return {
        'domain': kwargs.get("domain", []), 
        'fields': kwargs.get("fields", []), 
#         'offset': int(kwargs.get("offset", 0)), 
#         'limit': int(kwargs.get("limit", 0)), 
#         'order': kwargs.get("order", None), 
    }            
            
#     return {k:v for k,v in kwargs.items() if k in items}


def decode_bytes(result):
    if isinstance(result, (list, tuple)):
        decoded_result = []
        for item in result:
            decoded_result.append(decode_bytes(item))
        return decoded_result
    if isinstance(result, dict):
        decoded_result = {}
        for k, v in result.items():
            decoded_result[decode_bytes(k)] = decode_bytes(v)
        return decoded_result
    if isinstance(result, bytes):
        return result.decode('utf-8')
    return result


def extract_arguments(**kwargs):
    payloads = kwargs.get("payload", {})
    return {
        'domain': ast.literal_eval(payloads.get("domain", [])), 
        'fields': ast.literal_eval(payloads.get("fields", [])), 
        'offset': int(payloads.get("offset", 0)), 
        'limit': int(payloads.get("limit", 0)), 
        'order': payloads.get("order", None), 
    }