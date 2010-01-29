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
