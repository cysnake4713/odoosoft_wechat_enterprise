__author__ = 'cysnake4713'
# coding=utf-8
from odoo import tools
from odoo import models, fields, api
from odoo.tools.translate import _
from wechatpy.enterprise import WeChatClient


class WechatAccount(models.Model):
    _name = 'odoosoft.wechat.enterprise.account'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    corp_id = fields.Char('CorpID', required=True)
    corpsecret = fields.Char('Corpsecret', required=True)

    _sql_constraints = [('wechat_account_code_unique', 'unique(code)', _('code must be unique !'))]

    @api.model
    @tools.ormcache(skiparg=3)
    def get_client_by_code(self, code):
        account = self.search([('code', '=', code)])
        if account:
            return WeChatClient(account.corp_id, account.corpsecret)
        else:
            return None

    @api.multi
    @tools.ormcache()
    def get_client(self):
        return WeChatClient(self.corp_id, self.corpsecret)


class WechatApplication(models.Model):
    _name = 'odoosoft.wechat.enterprise.application'

    name = fields.Char('Name', required=True)
    application_id = fields.Integer('Application ID', required=True)
    code = fields.Char('Code', required=True)
    token = fields.Char('Token')
    ase_key = fields.Char('EncodingAESKey')
    account = fields.Many2one('odoosoft.wechat.enterprise.account', 'Enterprise Account', required=True)
    filters = fields.One2many('odoosoft.wechat.enterprise.filter', 'application', 'Filters')
    url = fields.Char('Callback url', compute='_compute_url')

    _sql_constraints = [('wechat_app_code_unique', 'unique(code)', _('code must be unique !'))]

    @api.multi
    @api.depends('code')
    def _compute_url(self):
        address = self.env['ir.config_parameter'].get_param('wechat.base.url')
        for app in self:
            app.url = '%s/wechat_enterprise/%s/api' % (address, app.code)

    @api.multi
    def process_request(self, msg):
        # find match filter
        if msg.type == 'event':
            match_filters = self.filters.search(
                [('type', '=', 'event'), ('event_type', '=', msg.event), ('active', '=', True), ('is_template', '=', False)])
        else:
            match_filters = self.filters.search([('type', '=', msg.type), ('active', '=', True), ('is_template', '=', False)])

        for a_filter in match_filters:
            result = a_filter.process(msg)
            if result[0]:
                return result[1]
        else:
            return None
