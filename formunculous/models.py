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

from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from django.contrib.localflavor.us.forms import USStateSelect
from django.contrib.localflavor.us.models import PhoneNumberField

from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from django import forms
from django.conf import settings

from formunculous.widgets import *
from formunculous.storage import *
from formunculous import fields

import datetime


# Application Definition Models
class CurrentManager(models.Manager):

    def current(self, **kwargs):
        return self.get_query_set().filter(
            start_date__lte=datetime.datetime.now(),
            stop_date__gte=datetime.datetime.now(),
            parent = None, sites=Site.objects.get_current(), **kwargs
            )

    def reviewer(self, user, **kwargs):
        return self.get_query_set().filter( reviewers=user, email_only=False,
                                            parent = None,
                                            sites=Site.objects.get_current(),
                                            **kwargs)

class ApplicationDefinition(models.Model):


    # Site differentiation
    try: 
        sid = settings.SITE_ID 
    except AttributeError: 
        from django.core.exceptions import ImproperlyConfigured 
        raise ImproperlyConfigured("You're using the Django \"sites framework\"\
                           without having set the SITE_ID setting. Create a site\
                           in your database and set the SITE_ID setting to fix\
                            this error.") 

    sites = models.ManyToManyField(Site, default=(sid,))


    # Add an optional recursive relation to enable creating sub forms
    # to create one-to-many relations for applications
    parent = models.ForeignKey('self', null=True, blank=True)

    name = models.CharField(max_length=150)
    owner = models.EmailField(_('Owner E-mail'))
    notify_owner = models.BooleanField(help_text="Email the owner each time \
                     an application is submitted")

    slug = models.SlugField(_('slug'),unique=True)
    description = models.TextField(blank=True)

    start_date = models.DateTimeField(default=datetime.datetime.now(),
                                      help_text=_("The date the application \
                                      will first be visible to user."))
    stop_date = models.DateTimeField(default=datetime.datetime.now(), 
                                     help_text=_("The date the application \
                                     will no longer be available to be \
                                     filled out"))

    authentication = models.BooleanField(help_text=_("Require the applicant \
                              to authenticate before using the application?"))

    # New in 1.2 (requires sql patch for existing installs)
    authentication_multi_submit = models.BooleanField(
        "Multiple Submissions (Authenticated)",
        help_text="Allow an authenticated user to submit multiple forms\
                   (applicable only if the form requires authentication")

    reviewers = models.ManyToManyField(User, null=True, blank=True)
    notify_reviewers = models.BooleanField(help_text="Email every reviewer each\
                          time an application is submitted")

    email_only = models.BooleanField(help_text=_("If checked, completed \
                          applications will not be stored in the database but \
                          emailed to the owner/reviewers (dependent on whether \
                          those notification flags are set"))

    objects = CurrentManager()

    class Meta:
        ordering = ["stop_date"]

    def __unicode__(self):
        return( u'%s' % self.name )

    def is_active(self):
        now = datetime.datetime.now()
        if now >= self.stop_date or now <= self.start_date:
            return False
        else:
            return True

class SubApplicationDefinition(models.Model):

    # Get subform name and slug from the ApplicationDefinition
    app_definition = models.ForeignKey(ApplicationDefinition)

    min_entries = models.IntegerField(default = 0, 
                                      help_text = _("The minimum number of\
                                               instances of this sub-form the\
                                               user must fill out.  0 if none."))
    max_entries = models.IntegerField(default = 0,
                                      help_text = _("The maximum number of\
                                               instances of this sub-form the\
                                               user must fill out. 0 if\
                                               there is no limit."))

    extras = models.IntegerField(default = 3, 
                                 help_text = _("The number of extra forms to\
                                                show by default on an\
                                                application"))
    

# Application data types/fields


class FieldDefinition(models.Model):

    """
    The base model for data type field definitions.
    """
    field_types = ()

    type = models.CharField(_('Type'),max_length=250,)
    application = models.ForeignKey(ApplicationDefinition)
    pre_text = models.TextField(blank = True, 
                                help_text=_("The html here is prepended \
                                             to the form field."))
    post_text = models.TextField(blank = True,
                                 help_text=_("The html here is appended \
                                              to the form field."))

    page = models.IntegerField(default=1)
    order = models.IntegerField()
    group = models.BooleanField(default=False, 
                                help_text=_("Group this with nearby\
                                      fields using an indented and \
                                      colored background."))

    label = models.CharField(max_length=250) 
    slug = models.SlugField()

    help_text = models.TextField(blank = True,
                                 help_text=_("The text here is added \
                                              to the defined field to help the \
                                              user understand its purpose."))

    require = models.BooleanField(default=True, 
                                  help_text=_("This requires that value be \
                                         entered for this field on \
                                         the application form."))
    reviewer_only = models.BooleanField(help_text=_("Make this field viewable\
                    only to the reviewer of an application, not the applicant."))
    header = models.BooleanField(default=True,
                                 help_text=_("If this is set to true the field\
                                              will be used as a header in the\
                                            reviewer view."))

    # New in 1.2 (requires sql patch for existing installs)

    multi_select = models.BooleanField(_("Allow Multiple Selections"),
                       help_text=_("If selected, the user\
                                   will be allowed to check multiple\
                                   options from dropdown selections.  Be\
                                   careful about which field type this is\
                                   used for (generally only use large\
                                   text area fields)."))

    use_radio = models.BooleanField(_("Use Radio Buttons"),
                       help_text=_("Dropdown selections\
                                   will be represented with radio buttons\
                                   for single select dropdowns and\
                                   check boxes for multi-select.\
                                   "))

    class Meta:
        ordering = ['page', 'order']

        
    def __unicode__(self):
        return( u'%s.%s: %s' % (self.page, self.order, self.label) )



class DropDownChoices(models.Model):

    field_definition = models.ForeignKey(FieldDefinition)
    text = models.CharField(max_length = 255)
    value = models.CharField(max_length = 255)

    class Meta:
        ordering = ['text']

# Instance Models (field and application)

class Application(models.Model):

    # Add an optional recursive relation to enable creating sub forms
    # to create one-to-many relations for applications
    parent = models.ForeignKey('self', null=True, blank=True)

    user = models.ForeignKey(User, blank=True, null=True)
    submission_date = models.DateTimeField(null=True, blank=True)
    app_definition = models.ForeignKey(ApplicationDefinition)

    def get_field_values(self, reviewer_fields=False, all_fields=False):
        """
        Returns a collection of dictionary objects with the field names
        and their values.

        By default this does not include the reviewer only fields that
        are in the application definition. To get those, pass True
        into the function.
        """
        fields = []
        if not all_fields:
            field_set = self.app_definition.fielddefinition_set.filter(
                reviewer_only=reviewer_fields)
        else:
            field_set = self.app_definition.fielddefinition_set.all()

        for field_def in field_set:
            field_model = eval(field_def.type)
            try:
                field_val = field_model.objects.get( app = self,
                                                     field_def = field_def)
                field_dict = {'label': field_def.label,
                              'data': field_val.value,},
            except:
                field_dict = {'label': field_def.label, 'data': None,},

            fields += field_dict
        return fields

    def get_field_value(self, field_slug):
        """
           Gets the value of the field defined by the slug given for this
           application instance, or returns None if either the value
           or the field definition is not found.
        """
        try:
            field_def = FieldDefinition.objects.get(
                             slug=field_slug, 
                             application=self.app_definition)
        except FieldDefinition.DoesNotExist:
            return None

        field_model = eval(field_def.type)

        try:
            field_val = field_model.objects.get( app = self, 
                                                 field_def=field_def )
        except field_model.DoesNotExist:
            return None

        return field_val.value


# Define empty permission model for using builder
class Form(models.Model):

    class Meta:
        permissions = (
            ("can_delete_applications", "Can delete applications"),
        )

class BaseField(models.Model):
    """
       This is the base model for all field types  Each unique field type
       must extend this model for the field to work properly.
    """
    
    name = 'Base'

    field_def = models.ForeignKey(FieldDefinition)
    app = models.ForeignKey(Application)

    allow_dropdown = False

class TextField(BaseField):
    """
       This is max length (most DBs) generic text field that has no
       input restrictions.
    """

    FieldDefinition.field_types+=('TextField','Text Input',),

    name = 'Text Input'
    value = models.CharField(max_length=255, blank=True, null=True)

    widget = None

    allow_dropdown = True


class TextArea(BaseField):
    """
       This is the large text area field.
    """
    
    FieldDefinition.field_types+=('TextArea', 'Large Text Area',),

    name= "Large Text Area"
    value = models.TextField(blank=True, null=True)

    widget = None
    allow_dropdown = True

class BooleanField(BaseField):
    """
       A simple yes/no field.
    """

    FieldDefinition.field_types+=('BooleanField', 'Yes/No Question',),

    name = "Yes/No Question/Checkbox"
    value = models.BooleanField(blank=True, default=False)

    widget = None
    allow_dropdown = False

class DateField(BaseField):
    """
       Uses a nice jquery widget for selecting a date.
    """
    FieldDefinition.field_types+=('DateField', 'Date Input',),

    name = "Date Input"
    value = models.DateField(blank=True, null=True)

    widget = DateWidget
    allow_dropdown = True

class EmailField(BaseField):
    """
      Builtin email field 
    """
    FieldDefinition.field_types+=('EmailField', 'Email Address',),

    name = "Email Address"
    value = models.EmailField(blank=True, null=True)

    widget = None
    allow_dropdown = True

class FloatField(BaseField):
    """
      Float field.  Accepts any decimal number basically
    """
    FieldDefinition.field_types+=('FloatField', 'Decimal Number',),

    name = "Decimal Number Field"
    value = models.FloatField(blank=True, null=True)

    widget = None
    allow_dropdown = True

class IntegerField(BaseField):
    """
      Integer field.  Accepts any whole number + or -
    """
    FieldDefinition.field_types+=('IntegerField', 'Whole Number',),

    name = "Whole Number Field"
    value = models.IntegerField(blank=True, null=True)

    widget = None
    allow_dropdown = True

class USStateField(BaseField):

    """
    Provides a dropdown selection of U.S. States and
    provinces.
    """

    FieldDefinition.field_types+=('USStateField', 'U.S. States',),

    name = "U.S. States"
    value = models.CharField(null=True, blank=True, 
                             max_length="255")

    widget = OptionalStateSelect
    allow_dropdown = False

class USZipCodeField(BaseField):

    FieldDefinition.field_types+=('USZipCodeField', 'U.S. Zipcode',),
    
    name = "U.S. Zipcode"
    value = fields.USZipCodeModelField(null=True, blank=True)

    widget = None
    allow_dropdown = True

class USPhoneNumber(BaseField):

    FieldDefinition.field_types+=('USPhoneNumber', 'U.S. Phone Number',),
    
    name = "U.S. Phone Number"
    value = PhoneNumberField(null=True, blank=True)

    widget = None
    allow_dropdown = True

class IPAddressField(BaseField):
    """
      IP address field field.  Accepts any valid IPv4 address.
    """
    FieldDefinition.field_types+=('IPAddressField', 'IP Address',),

    name = "IP Address"
    value = models.IPAddressField(blank=True, null=True)

    widget = None
    allow_dropdown = True

class PositiveIntegerField(BaseField):
    """
      Integer field.  Accepts any whole number that is positive
    """
    FieldDefinition.field_types+=('PositiveIntegerField', 
                                  'Positive Whole Number',),

    name = "Positive Whole Number Field"
    value = models.PositiveIntegerField(blank=True, null=True)

    widget = None
    allow_dropdown = True

class URLField(BaseField):
    """
      URL field.  Accepts any valid URL
    """
    FieldDefinition.field_types+=('URLField', 'URL',),

    name = "URL"
    value = models.URLField(blank=True, null=True)

    widget = None
    allow_dropdown = True
    

# File Based Fields

class FileField(BaseField):
    """
       This field accepts any file, regardless of type, and size
       is limited by the Django settings
    """

    FieldDefinition.field_types+=('FileField','File Upload',),

    name = 'File Upload'
    value = models.FileField(upload_to=upload_to_path, 
                             storage=ApplicationStorage(),
                             blank=True, null=True)
    widget = FileWidget
    allow_dropdown = False

class ImageField(BaseField):
    """
       This is a file field that only accepts common image formats.
    """

    FieldDefinition.field_types+=('ImageField','Picture Upload',),

    name = 'Picture Upload'
    value = models.ImageField(upload_to=upload_to_path, 
                             storage=ApplicationStorage(),
                             blank=True, null=True)
    widget = FileWidget
    allow_dropdown = False

class DocumentField(BaseField):
    """
       Validates common document mime-types/extensions
    """

    FieldDefinition.field_types+=('DocumentField', 'Document Upload',),
    
    name = "Document Upload"
    value = fields.DocumentField(upload_to=upload_to_path, 
                             storage=ApplicationStorage(),
                             blank=True, null=True)
    widget = FileWidget
    allow_dropdown = False
