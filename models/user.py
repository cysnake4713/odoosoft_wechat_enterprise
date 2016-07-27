# coding=utf-8

import time
from openerp import tools
import logging
from openerp import models, fields, api, exceptions
from openerp.tools.translate import _
from wechatpy.enterprise import WeChatClient
from wechatpy.exceptions import WeChatClientException

__author__ = 'cysnake4713'
_logger = logging.getLogger(__name__)


class WechatUser(models.Model):
    _name = 'odoosoft.wechat.enterprise.user'
    _rec_name = 'login'

    state = fields.Selection([('1', 'Stared'), ('4', 'Not Stared'), ('2', 'Frozen'), ('10', 'Server No Match')], 'State', default='4')

    login = fields.Char('Login', required=True)
    name = fields.Char('Name', required=True)

    user = fields.Many2one('res.users', 'User', ondelete='cascade')
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')
    wechat_login = fields.Char('Wechat Account')

    job = fields.Char('Job')
    departments = fields.Many2many('odoosoft.wechat.enterprise.department', 'wechat_enterprise_department_user_rel', 'user_id', 'department_id',
                                   'Departments')

    account = fields.Many2one('odoosoft.wechat.enterprise.account', 'Account', required=True)

    active = fields.Boolean('Active', default=True)

    @api.onchange('user')
    def onchange_user(self):
        self.name = self.user.name
        self.mobile = self.user.mobile
        self.email = self.user.email
        self.wechat_login = self.user.wechat_login

    @api.one
    @api.constrains('wechat_login', 'mobile', 'email')
    def _check_wechat_info(self):
        if not self.wechat_login and not self.mobile and not self.email:
            raise exceptions.Warning(_('wechat_login, mobile, email can not be all none'))

    @api.one
    def create_wechat_account(self):
        if self.env['ir.config_parameter'].get_param('wechat.sync') == 'True':
            client = WeChatClient(self.account.corp_id, self.account.corpsecret)
            client.user.create(user_id=self.login, name=self.name, department=[d.id for d in self.departments] or [1], position=self.job,
                               mobile=self.mobile, email=self.email, weixin_id=self.wechat_login)

    @api.model
    def unlink_wechat_account(self, logins, account):
        if self.env['ir.config_parameter'].get_param('wechat.sync') == 'True':
            client = WeChatClient(account.corp_id, account.corpsecret)
            client.user.batch_delete(user_ids=logins)

    @api.multi
    def write_wechat_account(self):
        if self.env['ir.config_parameter'].get_param('wechat.sync') == 'True':
            for user in self:
                client = WeChatClient(user.account.corp_id, user.account.corpsecret)
                # is user exist
                wechat_user_info = client.user.get(user.login)
                # if exist, update
                remote_val = {
                    'name': user.name if user.name else wechat_user_info.get('name'),
                    'position': user.job if user.job else wechat_user_info.get('position'),
                    'mobile': user.mobile if user.mobile else wechat_user_info.get('mobile'),
                    'email': user.email if user.email else wechat_user_info.get('email'),
                    'weixin_id': user.wechat_login if user.wechat_login else wechat_user_info.get('weixinid'),
                    'department': [d.id for d in user.departments] or [1],
                }

                local_values = remote_val.copy()
                local_values['job'] = local_values['position']
                local_values['wechat_login'] = local_values['weixin_id']

                client.user.update(user_id=user.login, **remote_val)
                user.with_context(is_no_wechat_sync=True).write(local_values)

    @api.multi
    def write(self, vals):
        # self.check_account_unique()
        self.env.cr.execute('SAVEPOINT wechat_write')
        result = super(WechatUser, self).write(vals)
        if 'is_no_wechat_sync' not in self.env.context:
            try:
                self.write_wechat_account()
            except Exception, e:
                self.env.cr.execute('ROLLBACK TO SAVEPOINT wechat_write')
                raise exceptions.Warning(str(e))
        self.env.cr.execute('RELEASE SAVEPOINT wechat_write')
        return result

    @api.model
    def create(self, vals):
        self.env.cr.execute('SAVEPOINT wechat_create')
        if 'login' not in vals:
            vals['login'] = self.env['ir.sequence'].get('wechat.login')
        user = super(WechatUser, self).create(vals)
        if 'is_no_wechat_sync' not in self.env.context:
            try:
                user.create_wechat_account()
            except Exception, e:
                self.env.cr.execute('ROLLBACK TO SAVEPOINT wechat_create')
                raise exceptions.Warning(str(e))
        self.env.cr.execute('RELEASE SAVEPOINT wechat_create')
        return user

    @api.multi
    def check_account_unique(self):
        if self.ids:
            self.env.cr.execute("""
                    SELECT count(id), account FROM odoosoft_wechat_enterprise_user
                    WHERE id in %s
                    GROUP BY account
                """, (tuple(self.ids),))
            res = self.env.cr.fetchall()
            if len(res) > 1:
                raise exceptions.Warning(_("Can't delete two account's user in one time."))

    @api.multi
    def unlink(self):
        self.check_account_unique()
        self.env.cr.execute('SAVEPOINT wechat_unlink')
        logins = [u.login for u in self]
        if self.ids:
            account = self[0].account
        result = super(WechatUser, self).unlink()
        if 'is_no_wechat_sync' not in self.env.context and self.ids:
            try:
                self.unlink_wechat_account(logins, account)
            except Exception, e:
                self.env.cr.execute('ROLLBACK TO SAVEPOINT wechat_unlink')
                raise exceptions.Warning(str(e))
        self.env.cr.execute('RELEASE SAVEPOINT wechat_unlink')
        return result

    @api.multi
    def unlink_force(self):
        self.with_context(is_no_wechat_sync=True).unlink()

    @api.multi
    def create_force(self):
        try:
            self.create_wechat_account()
        except Exception, e:
            raise exceptions.Warning(str(e))

    @api.multi
    def write_force(self):
        try:
            self.write_wechat_account()
        except Exception, e:
            raise exceptions.Warning(str(e))

    @api.multi
    def button_invite(self):
        for user in self:
            try:
                user.account.get_client().user.invite(user_id=user.login)
            except WeChatClientException, e:
                if e.errcode == 60119:  # message: contact already joined
                    user.state = '1'
                else:
                    raise e

    @api.model
    def sync_wechat_server(self):
        """
        sync wechat server user info to local database
        """
        accounts = self.env['odoosoft.wechat.enterprise.account'].search([])
        for account in accounts:
            try:
                client = account.get_client()
                server_values = client.user.list(department_id=1, fetch_child=True)
                local_values = {v['login']: v for v in self.search_read([('account', '=', account.id)],
                                                                        ['state', 'login', 'name', 'mobile', 'email', 'wechat_login', 'job', ])}
                for server_value in server_values:
                    # if someone on server and in local
                    if server_value['userid'] in local_values:
                        login = server_value['userid']
                        temp_server_value = {
                            'wechat_login': server_value.get('weixinid', False),
                            'name': server_value['name'],
                            'mobile': server_value.get('mobile', False),
                            'job': server_value.get('position', False),
                            'email': server_value.get('email', False),
                            'state': str(server_value['status']),
                        }
                        temp_local_value = {
                            'wechat_login': local_values[login]['wechat_login'],
                            'name': local_values[login]['name'],
                            'mobile': local_values[login].get('mobile', False) or False,
                            'job': local_values[login].get('job', False) or False,
                            'email': local_values[login].get('email', False) or False,
                            'state': local_values[login]['state'],
                        }
                        # if have difference
                        if set(temp_server_value.items()) - set(temp_local_value.items()):
                            self.env['odoosoft.wechat.enterprise.user'].browse(local_values[login]['id']).with_context(
                                is_no_wechat_sync=True).write(temp_server_value)
                        # un registry local value
                        del local_values[login]
                    # if someone on server but not in local
                    else:
                        _logger.warning('miss match server user:%s', server_value['userid'])
                        self.env['odoosoft.wechat.enterprise.log'].log_info(u'同步服务器用户', u'服务器用户:%s没有在本机找到对应关系' % server_value['userid'])
                # if someone on local but not on server
                if local_values:
                    mismatch_ids = [v['id'] for v in local_values.values()]
                    self.with_context(is_no_wechat_sync=True).browse(mismatch_ids).write({'state': '10'})
            except WeChatClientException, e:
                _logger.error('Get error in sync from server', e)
                self.env['odoosoft.wechat.enterprise.log'].log_info(u'同步服务器用户', str(e))
        self.env['odoosoft.wechat.enterprise.log'].log_info(u'同步服务器用户', u'同步完成')


class WechatWizard(models.TransientModel):
    _name = 'odoosoft.wechat.enterprise.user.wizard'

    user = fields.Many2one('res.users', 'User')
    account = fields.Many2one('odoosoft.wechat.enterprise.account', 'Account', required=True)
    wechat_login = fields.Char('Wechat Account')
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')

    @api.one
    @api.constrains('wechat_login', 'mobile', 'email')
    def _check_wechat_info(self):
        if not self.wechat_login and not self.mobile and not self.email:
            raise exceptions.Warning(_('wechat_login, mobile, email can not be all none'))

    @api.model
    def default_get(self, fields_list):
        result = super(WechatWizard, self).default_get(fields_list)
        user = self.env['res.users'].search([('id', '=', self.env.context['active_id'])]).ensure_one()
        result['mobile'] = user.mobile
        result['email'] = user.email
        result['wechat_login'] = user.wechat_login
        result['user'] = user.id
        return result

    @api.multi
    def create_wechat_user(self):
        if self.mobile:
            self.user.mobile = self.mobile
        if self.email:
            self.user.email = self.email
        if self.wechat_login:
            self.user.wechat_login = self.wechat_login
        value = {
            'user': self.user.id,
            'account': self.account.id,
            'name': self.user.name,
            'wechat_login': self.user.wechat_login,
            'email': self.user.email,
            'mobile': self.user.mobile,
        }
        self.env['odoosoft.wechat.enterprise.user'].create(value)
        self.env['res.users'].with_context(is_no_wechat_sync=True).write({
            'wechat_login': self.user.wechat_login,
            'email': self.user.email,
            'mobile': self.user.mobile,
        })
        return True


class UserCreateWizard(models.TransientModel):
    _name = 'odoosoft.wechat.enterprise.user.batch.wizard'
    _rec_name = 'account'

    account = fields.Many2one('odoosoft.wechat.enterprise.account', 'Account', required=True)
    res_users = fields.Many2many('res.users', 'wechat_batch_res_user_rel', 'batch_id', 'user_id', 'Need Process Users')
    processed_users = fields.Many2many('res.users', 'wechat_batch_res_processed_user_rel', 'batch_id', 'user_id', 'Processed Users')
    create_users = fields.Many2many('odoosoft.wechat.enterprise.user', 'wechat_batch_user_rel', 'batch_id', 'user_id', 'Create Users')
    result = fields.Char('Result')

    @api.multi
    def button_batch_create(self):
        processed_users = []
        result = ''
        new_wechat_users = []
        for user in self.res_users:
            value = {
                'user': user.id,
                'account': self.account.id,
                'name': user.name,
                'wechat_login': user.wechat_login,
                'email': user.email,
                'mobile': user.mobile,
            }
            try:
                new_wechat_users += self.env['odoosoft.wechat.enterprise.user'].create(value)
                processed_users += user
            except Exception, e:
                result += '%s %s\n' % (user.name, str(e))

        value = {
            'res_users': [(3, u.id) for u in processed_users],
            'create_users': [(4, u.id) for u in new_wechat_users],
            'result': result or u'成功',
            'processed_users': [(4, u.id) for u in processed_users]
        }
        self.write(value)

        res = self.env['ir.actions.act_window'].for_xml_id('odoosoft_wechat_enterprise', 'action_wechat_batch_user')
        res['res_id'] = self[0].id
        return res

    @api.multi
    def button_batch_create_fast(self):
        processed_users = []
        result = ''
        new_wechat_users = []
        # create inactive user
        self.env.cr.execute('SAVEPOINT wechat_update_extend')
        for user in self.res_users:
            value = {
                'user': user.id,
                'account': self.account.id,
                'name': user.name,
                'wechat_login': user.wechat_login,
                'email': user.email,
                'mobile': user.mobile,
                'active': False,
            }
            try:
                new_wechat_users += self.env['odoosoft.wechat.enterprise.user'].create(value)
                processed_users += user
            except Exception, e:
                result += '%s %s\n' % (user.name, str(e))
        if result:
            self.env.cr.execute('ROLLBACK TO SAVEPOINT wechat_update_extend')
            value = {
                'result': result,
            }
        else:
            self.env.cr.execute('RELEASE SAVEPOINT wechat_update_extend')
            # create csv file depends on new user information
            csv_file = u'姓名,帐号,微信号,手机号,邮箱,所在部门,职位\n'
            for user in new_wechat_users:
                csv_file += u'%s,%s,%s,%s,%s,%s,\n' % (user.name, user.login, user.wechat_login or '', user.mobile or '', user.email or '', 1)
            csv_file = ('temp.csv', csv_file)
            # upload csv file
            client = WeChatClient(self.account.corp_id, self.account.corpsecret)
            media = client.media.upload(media_type='file', media_file=csv_file)
            app = self.env.ref('odoosoft_wechat_enterprise.application_default')
            job_id = client.batch.sync_user(encoding_aes_key=app.ase_key, media_id=media['media_id'], token=app.token, url=app.token)['jobid']
            value = {
                'res_users': [(3, u.id) for u in processed_users],
                'create_users': [(4, u.id) for u in new_wechat_users],
                'result': u'成功,请退出向导,等待一段时间后查看用户是否成功创建',
                'processed_users': [(4, u.id) for u in processed_users]
            }
        self.write(value)

        res = self.env['ir.actions.act_window'].for_xml_id('odoosoft_wechat_enterprise', 'action_wechat_batch_user')
        res['res_id'] = self[0].id
        return res


class WechatInviteWizard(models.TransientModel):
    _name = 'odoosoft.wechat.enterprise.user.batch.invite.wizard'
    _rec_name = 'account_id'
    _description = 'Batch Invite Wizard'

    account_id = fields.Many2one('odoosoft.wechat.enterprise.account', 'Account')
    user_ids = fields.Many2many('odoosoft.wechat.enterprise.user', 'invite_wizard_user_rel', 'invite_id', 'user_id', 'Need Invite Users')

    @api.model
    def default_get(self, fields_list):
        result = super(WechatInviteWizard, self).default_get(fields_list)
        users = self.env['odoosoft.wechat.enterprise.user'].search([('id', '=', self.env.context['active_ids']), ('state', '=', '4')])
        result['user_ids'] = [(6, 0, [u.id for u in users])]
        account_id = list(set([u.account.id for u in users]))
        if len(account_id) == 1:
            result['account_id'] = account_id[0]
        else:
            raise exceptions.Warning(_('Choose multi accounts users in one sync or no user need to be invited!'))
        return result

    @api.multi
    def button_batch_invite(self):
        app = self.env['odoosoft.wechat.enterprise.application'].search(
            [('account', '=', self.account_id.id), ('application_id', '=', 0)]).ensure_one()
        self.account_id.get_client().batch.invite_user(app.url, app.token, app.ase_key, [u.login for u in self.user_ids])
        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Invite Send'),
            'message': _('Invite Already send'),
        }
