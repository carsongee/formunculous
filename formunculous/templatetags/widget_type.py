#     This file is part of formunculous.
#
#     formunculous is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     formunculous is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with formunculous.  If not, see <http://www.gnu.org/licenses/>.
#     Copyright 2009-2013 Carson Gee

from django import template
from django.template import TemplateSyntaxError

register = template.Library()

class WidgetType(template.Node):
    def __init__(self, object_name, var_name = None):
        self.var_name = var_name

        self.object_name = template.Variable(object_name)

    def render(self,context):
        context[self.var_name] = self.object_name.resolve(context).__class__.__name__
        return ''
        



#@register.tag(widget_type)
def widget_type(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 4:
        raise TemplateSyntaxError, "%r takes three arguments" % bits[0]
    

    return WidgetType(bits[1], bits[3])


widget_type = register.tag(widget_type)
