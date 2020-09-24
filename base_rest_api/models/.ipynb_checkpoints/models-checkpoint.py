# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Base(models.AbstractModel):
    _inherit = 'base'
    
    _expose = False