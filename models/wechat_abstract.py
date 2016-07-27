__author__ = 'cysnake4713'

# coding=utf-8
from openerp import tools
from openerp import models, fields, api
from openerp.tools.translate import _


class WechatAbstract(models.AbstractModel):
    _name = 'wechat.enterprise.abstract'

    _description = 'Wechat Enterprise Abstract Model'

    @api.multi
    def send(self):
        wechat_code = self.env.context.get('wechat_code', [])
        users = self.env.context.get('message_users', '')
        user_ids = []
        if users:
            user_ids = users if isinstance(users, list) else [users]
        user_ids = filter(lambda a: a, user_ids)
        for code in wechat_code:
            for obj in self:
                values = {
                    'obj': obj,
                    'content': self.env.context.get('message', ''),
                    'code': code,
                    'user_ids': user_ids,
                    'type': self.env.context.get('wechat_type', 'text'),
                    'template': self.env.context.get('wechat_template', ''),
                    'title': self.env.context.get('wechat_title', None),
                }

                self.env['odoosoft.wechat.enterprise.message'].create_message(**values)
