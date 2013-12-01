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

from formunculous.models import *
from formunculous.forms import ApplicationForm
from formunculous.utils import build_template_structure, get_formsets

from django import template
from django.template import TemplateSyntaxError, Variable, Template
from django.template.defaultfilters import stringfilter

from django.template.loader import render_to_string
from django.utils.translation import ugettext as _




register = template.Library()

class RenderAsTemplate(template.Node):

    def __init__(self, variable):

        self.variable = Variable(variable)

    def render(self, context):

        to_render = self.variable.resolve(context)
        if to_render:
            t = Template(to_render)
        else:
            return ''

        return t.render(context)


def render_as_template(parser, token):
    """
      Takes a variable or string as an argument and renders the contents using
      the current context as a template.  Allowing for template tags and filters
      to be used in the passed in object
    """

    bits = list(token.split_contents())

    if len(bits) < 2:
        raise TemplateSyntaxError, _('%r tag requires at least one argument') % bits[0]

    return RenderAsTemplate(bits[1])

render_as_template = register.tag(render_as_template)



class FuncForm(template.Node):

    def __init__(self, ad_slug, var_name=None):
        self.var_name = var_name

        # If we don't get the application definition specified
        # fail silently and return "Form Unavailable"
        try:
            self.ad = ApplicationDefinition.objects.get(slug__exact = ad_slug)
        except:
            self.ad = None


    def render(self, context):

        if self.ad == None:
            return _("Form requested is unavailable")
        ad = self.ad

        form = None
        app = None

        if datetime.datetime.now() < ad.start_date \
                or datetime.datetime.now() > ad.stop_date:
            return _("This form is not active")

        if ad.applicationdefinition_set.all():
            return _("This tag does not support forms that have sub-forms")

        if ad.authentication:
            return _("This tag does not support authenticated forms")


        if not form:
            form = ApplicationForm(ad, app)

        fields = build_template_structure(form, ad)

        # Try a customized template.
        # if it is there use it, else use the default template.
        try:
            t = template.loader.get_template('formunculous/%s/apply.html' % ad.slug)
            t = 'formunculous/%s/tag_apply.html' % ad.slug
        except:
            t = 'formunculous/tag_apply.html'

        rendered = render_to_string(
            t,
            {'form': form, 'ad': ad, 'fields': fields,},
            context_instance=context)

        if self.var_name:
            context[self.var_name] = rendered
            return ''
        else:
            return rendered


def func_form(parser, token):
    """
    
    Takes a slug as an argument and an optional variable argument
    to render the specified form to the page or the variable depending.
    
    Useful for including func forms wherever you need to (poll in base.html
    or other similar uses).

    """

    bits = list(token.split_contents())

    if len(bits) < 2 or len(bits) == 3 or len(bits) > 4:
        raise TemplateSyntaxError, _('%r tag requires at least the form\'s slug as an argument with an optional variable "as blah" argument.')

    var_name = None
    if len(bits) == 4:
        var_name = bits[3]

    return FuncForm(bits[1], var_name)

func_form = register.tag(func_form)

#
# Adapted from http://djangosnippets.org/snippets/1461/
#

@register.filter
@stringfilter
def split_as_list(value, splitter='|', autoescape=None):
    return value.split(splitter)
