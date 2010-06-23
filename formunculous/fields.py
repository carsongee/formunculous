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

from django.forms import Field, FileField, MultipleChoiceField
from django.forms import ValidationError
from django.forms.fields import RegexField
from formunculous.widgets import HoneypotWidget
from django.db import models
from os.path import splitext
from django.utils.translation import ugettext_lazy as _

# The following doesn't work because it's init method does not
# accept the max_length and min_length parameters, and I get
# a multiple definition error because it has to be specified
# in the CharField model.
#from django.contrib.localflavor.us.forms import USZipCodeField

EMPTY_VALUES = (None, '',)

class HoneypotField(Field):
    """
    Creates a hidden text input field, that when validated, if the
    field has a different value in it than when initialized, the form
    is invalid.  This is used to stop simple SPAM bots.
    """

    widget = HoneypotWidget

    def clean(self, value):

        # If the value is empty or changed from the initial
        # invalidate the field.
        if (self.initial in EMPTY_VALUES and value \
            in EMPTY_VALUES) or value == self.initial:
            return value

        raise ValidationError('Honeypot field changed in value.')

class DocumentFormField(FileField):
    """A validating document upload field"""
    valid_content_types = ('text/html', 'text/plain', 'text/rtf',
                           'text/xml', 'application/msword',
                           'application/rtf', 'application/pdf')
    valid_file_extensions = ('odt', 'pdf', 'doc', 'docx', 'txt',
                             'html', 'rtf', 'htm', 'xhtml')

    def __init__(self, *args, **kwargs):
        super(DocumentFormField, self).__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        f = super(DocumentFormField, self).clean(data, initial)

        #Allow for null
        if not f:
            return f

        ext = splitext(f.name)[1][1:].lower()
        if ext in DocumentFormField.valid_file_extensions \
           and f.content_type in DocumentFormField.valid_content_types:
            return f
        raise ValidationError(_(u'Document types accepted: ') + ', '.join(DocumentFormField.valid_file_extensions))


class DocumentField(models.FileField):
    
    def formfield(self, **kwargs):
        defaults = {'form_class': DocumentFormField}
        defaults.update(kwargs)
        return super(DocumentField, self).formfield(**defaults)


class USZipCodeModelField(models.CharField):
    
    description = _("U.S. Zipcode XXXXX or XXXXX-XXXX")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 10)
        super(USZipCodeModelField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'form_class': USZipCodeField}

        defaults.update(kwargs)
        return super(USZipCodeModelField, self).formfield(**defaults)

class USZipCodeField(RegexField):
    default_error_messages = {
        'invalid': _('Enter a zip code in the \
                              format XXXXX or XXXXX-XXXX.'),
        }
	
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(USZipCodeField, self).__init__(r'^\d{5}(?:-\d{4})?$',
                                             max_length=None,
                                             min_length=None, 
                                             *args, **kwargs)


# This field is used for storing a multiple choice field into
# a string type field.
class MultipleChoiceToStringField(MultipleChoiceField):

    def clean(self, value):

        super(MultipleChoiceToStringField, self).clean(value)
        return ' | '.join(value)
