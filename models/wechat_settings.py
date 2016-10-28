__author__ = 'cysnake4713'
# coding=utf-8
from odoo import tools
from odoo import models, fields, api
from odoo.tools.translate import _


class DbConfigSettings(models.TransientModel):
    _name = 'odoosoft.wechat.config.settings'
    _inherit = 'res.config.settings'

    default_account = fields.Many2one('odoosoft.wechat.enterprise.account', 'Default User Page Account Value', default_model='odoosoft.wechat.enterprise.user')