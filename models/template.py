__author__ = 'cysnake4713'

# coding=utf-8
import logging
from openerp import tools
from openerp import models, fields, api
from openerp.tools.translate import _
import dateutil.relativedelta as relativedelta

_logger = logging.getLogger(__name__)
try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment

    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,  # do not output newline after blocks
        autoescape=True,  # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw: relativedelta.relativedelta(*a, **kw),
    })
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class MessageTemplate(models.Model):
    _name = 'odoosoft.wechat.enterprise.message.template'
    _rec_name = 'name'
    _description = 'Odoosoft Wechat Enterprise Template'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    title = fields.Char('Title')
    content = fields.Text('Content')
    url = fields.Char('URL')
    is_no_url = fields.Boolean('Is No Url', default=False)

    @api.multi
    def render(self, obj=None):
        # try to load the template
        template = mako_template_env.from_string(tools.ustr(self.content))
        variables = {
            'env': self.env,
            'object': obj,
            'ctx': self.env.context,
            'fields': obj._fields if obj else None,
        }
        return template.render(variables)
