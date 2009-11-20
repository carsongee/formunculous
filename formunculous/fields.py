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
#     Copyright 2009 Carson Gee

from django.forms import Field, FileField
from django.forms import ValidationError
from formunculous.widgets import HoneypotWidget
from django.db import models
from os.path import splitext
from django.utils.translation import ugettext_lazy as _

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
	
class DocumentValidationError(ValidationError):
    def __init__(self):
        super(DocumentValidationError, self).__init__(_(u'Document types accepted: ') + ', '.join(DocumentFormField.valid_file_extensions))


class DocumentFormField(FileField):
    """A validating document upload field"""
    valid_content_types = ('text/html', 'text/plain', 'text/rtf',
                           'text/xml', 'application/msword',
                           'application/rtf', 'application/pdf')
    valid_file_extensions = ('odt', 'pdf', 'doc', 'txt',
                             'html', 'rtf', 'htm', 'xhtml')

    def __init__(self, *args, **kwargs):
        super(DocumentFormField, self).__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        f = super(DocumentFormField, self).clean(data, initial)
        ext = splitext(f.name)[1][1:].lower()
        if ext in DocumentFormField.valid_file_extensions \
           and f.content_type in DocumentFormField.valid_content_types:
            return f
        raise DocumentValidationError()


class DocumentField(models.FileField):
    
    def formfield(self, **kwargs):
        defaults = {'form_class': DocumentFormField}
        defaults.update(kwargs)
        return super(DocumentField, self).formfield(**defaults)
