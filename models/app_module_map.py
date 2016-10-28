__author__ = 'cysnake4713'
# coding=utf-8
from odoo import tools
from odoo import models, fields, api
from odoo.tools.translate import _


class AppModuleMap(models.Model):
    _name = 'odoosoft.wechat.enterprise.map'
    _rec_name = 'code'

    code = fields.Char('Code', required=True)
    application = fields.Many2one('odoosoft.wechat.enterprise.application', 'Enterprise Application')

    _sql_constraints = [('wechat_map_code_unique', 'unique(code)', _('code must be unique !'))]

    @api.model
    def get_map(self, code):
        return self.search([('code', '=', code)]).application