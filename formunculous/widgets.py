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

from django import forms

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.conf import settings

from django.contrib.localflavor.us.us_states import STATE_CHOICES
from django.forms.fields import Select

class FileWidget(forms.FileInput):

    def __init__(self, attrs={}):
        super(FileWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []

        output.append(super(FileWidget, self).render(name, value, attrs))
        if value and hasattr(value, "url"):
            output.append('<div class="apply_file_url">%s <br /><a target="_blank" href="%s">%s</a></div> ' % \
                (_('Currently:'), value.url, value, ))

        return mark_safe(u''.join(output))

class DateWidget(forms.TextInput):
    class Media:
        js = (
              settings.MEDIA_URL + "formunculous/js/jquery-1.3.2.min.js",
              settings.MEDIA_URL + "formunculous/js/jquery-ui-1.7.2.custom.min.js",
              settings.MEDIA_URL + "formunculous/js/datepick.js",
              )
        css = {
            'all': (settings.MEDIA_URL + "formunculous/css/smoothness/jquery-ui-1.7.2.custom.css",),
            }

    def __init__(self, attrs={}):
        super(DateWidget, self).__init__(attrs={'class': 'vDateField', 'size': '8'})

class HoneypotWidget(forms.TextInput):
    """
    Creates a hidden text input field, that when validated, if the
    field has a different value in it than when initialized, the form
    is invalid.  This is used to stop simple SPAM bots.
    """
	 
    is_hidden = True
    def __init__(self, attrs=None, *args, **kwargs):
        super(HoneypotWidget, self).__init__(attrs, *args, **kwargs)
        if not self.attrs.has_key('class'):
            self.attrs['style'] = 'display:none'

    def render(self, *args, **kwargs):
        value = super(HoneypotWidget, self).render(*args, **kwargs)
        return value

class OptionalStateSelect(Select):
   """
   A Select widget that uses a list of U.S. states/territories as its choices.
   From the django project but a null option is prepended to the list.
   """
   def __init__(self, attrs=None):
       states_with_blank = tuple([('', '-----------')] + list(STATE_CHOICES))
       super(OptionalStateSelect, self).__init__(attrs, choices=states_with_blank)
