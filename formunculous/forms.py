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

from django import forms
from django.db import models
from django.utils.safestring import mark_safe
from django.forms.util import ErrorList
from formunculous.models import *
from formunculous.fields import HoneypotField
from django.utils.translation import ugettext as _
from django.forms import ModelForm

class ApplicationForm(forms.Form):

    def __init__(self, app_def, app=None, reviewer=False, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.app_def = app_def
        self.app = app
        self.reviewer = reviewer

        field_set = app_def.fielddefinition_set.filter(reviewer_only=self.reviewer)
        # Loop through the application field definition set
        # and create form fields for them.
        for field_def in field_set:
            
            # eval the model defined in type to get it's django field
            # add that and the label specified in the FieldDefinition

            # Intentionally not catching the potential exceptions here, let
            # them bubble up
            field_model = eval(field_def.type)
            data = None
            
            try:
                # Grab the model if this value is already stored otherwise, ignore
                field_model = field_model.objects.get(field_def = field_def,
                                                      app = self.app)
                data = field_model.value
            except field_model.DoesNotExist:
                pass

            field_def_choices = field_def.dropdownchoices_set.all()
            if field_def_choices:
                choices = (())
                for choice in field_def_choices:
                    choices += (choice.value, choice.text,),
                form_field = forms.ChoiceField(choices = choices)
            else:
                form_field = field_model._meta.get_field('value').formfield()
                # Custom field widgets
                if field_model.widget:
                    attrs = form_field.widget.attrs
                    form_field.widget = field_model.widget(attrs = attrs)

            form_field.required = False # Will check required on final submission
            form_field.label = mark_safe(field_def.label)
            form_field.initial = data
            form_field.help_text = mark_safe(field_def.help_text)

            # Add it to the growing fieldset
            self.fields[field_def.slug] = form_field
            
        # Create a honeypot field automatically
        if not self.fields.has_key('company'):
            self.fields['company'] = HoneypotField()
        else:
            i = 0
            while self.fields.has_key('company%s' % i):
                i+=1
            self.fields['company%s' % i] = HoneypotField()

    def save(self):
        """
        This is used for interim saves, and will save all data in the form
        """
        
        # Save the app first
        self.app.save()

        # Go through the fieldset and save the values
        field_set = self.app_def.fielddefinition_set.filter(reviewer_only=self.reviewer)

        for field_def in field_set:
            field_model = eval(field_def.type)
            try:
                field_model = field_model.objects.get(field_def = field_def,
                                                      app = self.app)
            except field_model.DoesNotExist:
                field_model = field_model(field_def = field_def, app = self.app)

            true_field = field_model._meta.get_field('value')
            true_field.save_form_data(field_model, 
                                      self.cleaned_data[field_def.slug])
            field_model.save()
    
    def check_required(self):
        """
           Checks for field definitions that have been marked with the
           required field.  If they are empty or blank, update
           the fields with errors.
        """

        if not self.is_bound:
            # Probably should throw an exception
            return False

        ret_val = True

        field_set = self.app_def.fielddefinition_set.filter(reviewer_only=self.reviewer)
        for field_def in field_set:
            if field_def.require:
                if self.cleaned_data[field_def.slug] == None \
                        or self.cleaned_data[field_def.slug] == '':
                    # Before assuming that because the field isn't saved, grab
                    # the value from the model to see if it actually is.
                    fv = self.app.get_field_value(field_def.slug)
                    if not fv:
                        self._errors[field_def.slug] = ErrorList([_('This field requires a value before the form can be submitted'),])
                        del self.cleaned_data[field_def.slug]
                        ret_val = False
        return ret_val
        
class ApplicationDefinitionForm(ModelForm):

    start_date = forms.DateTimeField(widget=DateWidget)
    stop_date = forms.DateTimeField(widget=DateWidget)

    class Meta:
        model = ApplicationDefinition

class FieldDefinitionForm(ModelForm):

    type = forms.CharField(max_length=250,
                widget=forms.Select(choices=FieldDefinition.field_types),
                           initial=FieldDefinition.field_types[0][0])
    order = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = FieldDefinition
