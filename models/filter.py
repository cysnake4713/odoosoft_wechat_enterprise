__author__ = 'cysnake4713'
# coding=utf-8
from odoo import tools
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval as eval
from wechatpy.enterprise import replies
import re


class WechatFilter(models.Model):
    _name = 'odoosoft.wechat.enterprise.filter'

    _order = 'sequence'

    name = fields.Char('Name', copy=False)
    sequence = fields.Integer('Sequence', default=10)
    type = fields.Selection([('text', 'Text'),
                             ('image', 'Image'),
                             ('voice', 'Voice'),
                             ('video', 'Video'),
                             ('location', 'Location'),
                             ('event', 'Event'),
                             ], 'Message Type', default='text', required=True)
    event_type = fields.Selection([('subscribe', 'subscribe'),
                                   ('unsubscribe', 'unsubscribe'),
                                   ('location', 'LOCATION'),
                                   ('click', 'CLICK'),
                                   ('view', 'VIEW'),
                                   ('scancode_push', 'scancode_push'),
                                   ('scancode_waitmsg', 'scancode_waitmsg'),
                                   ('pic_sysphoto', 'pic_sysphoto'),
                                   ('pic_photo_or_album', 'pic_photo_or_album'),
                                   ('location_select', 'location_select'),
                                   ('enter_agent', 'enter_agent'),
                                   ('batch_job_result', 'batch_job_result'),
                                   ], 'Event Type')
    match = fields.Text('Match')
    reply_type = fields.Selection([('text', 'Text'),
                                   ('image', 'Image'),
                                   ('voice', 'Voice'),
                                   ('video', 'Video'),
                                   ('news', 'News'),
                                   ], 'Reply Type', default='text', required=True)
    action = fields.Text('Action')
    application = fields.Many2one('odoosoft.wechat.enterprise.application', copy=False)
    template = fields.Many2one('odoosoft.wechat.enterprise.message.template', 'Template')
    active = fields.Boolean('Is Active', default=True)
    is_template = fields.Boolean('Is Template', default=False, copy=False)
    is_system = fields.Boolean('Is System', default=False)

    _defaults = {
        'match': """# self: 当前self引用
# msg: 传入的消息内容(msg.type, msg.content)
# result : 返回值，True 或者 False
# context： 传送给 action 的 context
# re : 正则 re 包
result = True
""",
        'action': """# self: 当前self引用
# msg: 传入的消息内容
# reply : 返回给用户的结果
# context： 接收的context
# template：当前filter定义的模板
""",
    }

    @api.multi
    def process(self, msg):
        match_context = {
            'self': self,
            'msg': msg,
            'result': False,
            'context': {},
            're': re,
        }
        if self.match:
            eval(self.match, match_context, mode="exec", nocopy=True)
        if match_context['result']:
            reply_context = {}
            action_context = {
                'self': self,
                'msg': msg,
                'reply': reply_context,
                'context': match_context['context'],
                'template': self.template
            }
            eval(self.action, action_context, mode="exec", nocopy=True)
            # build reply
            if self.reply_type != 'news':
                reply_context['message'] = msg
                reply = replies.REPLY_TYPES[self.reply_type](**reply_context)
            else:
                reply = replies.ArticlesReply(message=msg)
                for article in reply_context['articles']:
                    reply.add_article(article)
            return True, reply
        else:
            return False, None
