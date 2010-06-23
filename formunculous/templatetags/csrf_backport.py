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
#     Copyright 2009,2010 Carson Gee

from django import template


# This is just to make formunculous works in any Django version 1.1 and up.
# it is registered in the __init__ for formunculous if we are using a version
# that doesn't have this tag.

register = template.Library()

class CsrfTokenNode(template.Node):
    # This no-op tag exists to allow 1.1.X code to be compatible with Django 1.2
    def render(self, context):
        return u''

def csrf_token(parser, token):

    return CsrfTokenNode()

register.tag(csrf_token)
