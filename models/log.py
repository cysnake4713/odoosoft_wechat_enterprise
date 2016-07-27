# coding=utf-8
__author__ = 'cysnake4713'
from openerp import tools
from openerp import models, fields, api
from openerp.tools.translate import _


class WechatFilterErrorLog(models.Model):
    _name = 'odoosoft.wechat.enterprise.log'
    _order = 'create_date desc'

    name = fields.Char('Name')
    message = fields.Char('Message')
    create_date = fields.Datetime('Create Datetime')

    @api.model
    def log_info(self, name, message):
        self.sudo().create({'name': name, 'message': message})
