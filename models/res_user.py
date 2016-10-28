__author__ = 'cysnake4713'
# coding=utf-8
from odoo import tools, exceptions
from odoo import models, fields, api
from odoo.tools.translate import _


class ResUserInherit(models.Model):
    _inherit = 'res.users'

    wechat_user = fields.One2many('odoosoft.wechat.enterprise.user', 'user', 'Wechat Account')
    wechat_login = fields.Char('Wechat Account')

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights on
        display_employees_suggestions fields. Access rights are disabled by
        default, but allowed on some specific fields defined in
        self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        init_res = super(ResUserInherit, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        self.SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        self.SELF_WRITEABLE_FIELDS.extend(['wechat_login', 'wechat_user'])
        # duplicate list to avoid modifying the original reference
        self.SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        self.SELF_READABLE_FIELDS.extend(['wechat_login', 'wechat_user'])
        return init_res

    @api.multi
    def unlink(self):
        for user in self:
            user.wechat_user.sudo().unlink()
        res = super(ResUserInherit, self).unlink()
        return res

    @api.multi
    def write(self, vals):
        self.env.cr.execute('SAVEPOINT user_write')
        result = super(ResUserInherit, self).write(vals)
        if ('mobile' in vals or 'wechat_login' in vals or 'email' in vals) and 'is_no_wechat_sync' not in self.env.context:
            try:
                for user in self:
                    user.wechat_user.sudo().write({
                        'user': user.id,
                        'wechat_login': user.wechat_login,
                        'email': user.email,
                        'mobile': user.mobile,
                    })
            except Exception, e:
                self.env.cr.execute('ROLLBACK TO SAVEPOINT user_write')
                raise exceptions.Warning(str(e))
        self.env.cr.execute('RELEASE SAVEPOINT user_write')
        return result

