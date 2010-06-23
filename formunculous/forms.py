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
from django.db import models
from django.utils.safestring import mark_safe
from django.forms.util import ErrorList
from formunculous.models import *
from formunculous.fields import HoneypotField, MultipleChoiceToStringField
from django.utils.translation import ugettext as _
from django.forms import ModelForm
from django.forms.widgets import RadioSelect, Select, SelectMultiple, CheckboxSelectMultiple, HiddenInput

from django.forms.formsets import BaseFormSet, TOTAL_FORM_COUNT, INITIAL_FORM_COUNT, ORDERING_FIELD_NAME, DELETION_FIELD_NAME, ManagementForm


class ApplicationForm(forms.Form):

    def __init__(self, app_def, app=None, reviewer=False, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.app_def = app_def
        self.app = app
        self.reviewer = reviewer

        # If there is an application defined, add it's pk
        if app:
            pk_field = forms.IntegerField(initial=app.id, widget=HiddenInput)
            pk_field.is_hidden = True
            pk_field.required = False
            self.fields['pk'] = pk_field

        field_set = app_def.fielddefinition_set.filter(
            reviewer_only=self.reviewer)
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
                # Grab the model if this value is already stored otherwise,
                # ignore
                field_model = field_model.objects.get(field_def = field_def,
                                                      app = self.app)
                data = field_model.value
            except field_model.DoesNotExist:
                pass

            # If there are dropdown choices specified, create the
            # choices tuple for use in the field determined by other
            # user choices.
            field_def_choices = field_def.dropdownchoices_set.all()
            if field_def_choices and field_model.allow_dropdown:
                choices = (())
                for choice in field_def_choices:
                    choices += (choice.value, choice.text,),

                # Users are allowed to specify that a choiced
                widget = Select
                if field_def.multi_select:
                    # Fix the data from being stored as a string to
                    # being stored as a list
                    if data:
                        try:
                            data = data.split(' | ')
                        except:
                            data = None
                    widget = SelectMultiple
                    if field_def.use_radio:
                        widget = CheckboxSelectMultiple
                if field_def.use_radio and not field_def.multi_select:
                    widget = RadioSelect

                if field_def.multi_select:
                    form_field = MultipleChoiceToStringField(
                        choices = choices, widget = widget)
                else:
                    form_field = forms.ChoiceField(choices=choices,
                                             widget = widget)
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
        field_set = self.app_def.fielddefinition_set.filter(
            reviewer_only=self.reviewer)

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

        if not hasattr(self, 'cleaned_data'):
            return False

        ret_val = True

        field_set = self.app_def.fielddefinition_set.filter(
            reviewer_only=self.reviewer)

        for field_def in field_set:

            if field_def.require:
                # If the field isn't clean, don't bother checking
                if not self.cleaned_data.has_key(field_def.slug):
                    self._errors[field_def.slug] = ErrorList([_('This field requires a value before the form can be submitted'),])
                    ret_val = False
                    continue
                if self.cleaned_data[field_def.slug] == None \
                        or self.cleaned_data[field_def.slug] == '':
                    # Before assuming that because the field isn't saved, grab
                    # the value from the model to see if it actually is.
                    fv = None
                    if self.app:
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


class FormunculousBaseFormSet(BaseFormSet):

    def __init__(self, app_def=None, user=None, reviewer=False, parent=None,
                 minimum=0, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList):
        self.app_def = app_def
        self.user = user
        self.reviewer = reviewer
        self.parent = parent
        self.minimum = minimum


        # Make sure we have at least minimum number of forms:
        if not ( data or files ):
            apps = Application.objects.filter(user = self.user, 
                                              parent = self.parent,
                                              app_definition = self.app_def)
            initial_count = apps.count()
            total = initial_count + self.extra
            if total < self.minimum:
                self.extra = self.minimum - initial_count

        super(FormunculousBaseFormSet, self).__init__(data, files, auto_id,
                                               prefix, initial, error_class)

    def initial_form_count(self):
        """Returns the number of forms that are required in this FormSet."""
        if not (self.data or self.files):
            apps = Application.objects.filter(user = self.user, 
                                              parent = self.parent,
                                              app_definition = self.app_def)
            return apps.count()
        return super(FormunculousBaseFormSet, self).initial_form_count()

    def _construct_form(self, i, **kwargs):
        """
        Instantiates and returns the i-th form instance in a formset.
        """
        defaults = {'auto_id': self.auto_id, 
                    'prefix': self.add_prefix(i)}
        if self.data or self.files:
            defaults['data'] = self.data
            defaults['files'] = self.files
        if self.initial:
            try:
                defaults['initial'] = self.initial[i]
            except IndexError:
                pass

        # Allow extra forms to be empty.
        if i >= self.initial_form_count():
            defaults['empty_permitted'] = True
        defaults.update(kwargs)

        app = None
        # Grab the proper app if this is an already existing instance
        if i < self.initial_form_count():
            
            # If the form is already posted, grab the PK
            # from it, instead of relying on a query
            if self.is_bound:
                pk_key = "%s-%s" % (self.add_prefix(i), 'pk')
                pk = int(self.data[pk_key])
                app = Application.objects.get(id=pk)

            else:
                apps = Application.objects.filter(
                    user = self.user, 
                    parent = self.parent,
                    app_definition = self.app_def).order_by("id")
                app = apps[i]
            

        form = self.form(self.app_def, app, self.reviewer, **defaults)
        self.add_fields(form, i)
        return form
            
        
# This is a straight rip of the standard formset_factory, but customized
# to handle the Django 1.2 formset backwards incompatible fix
def formunculous_subformset_factory(form, formset=BaseFormSet, extra=1, 
                                    can_order=False, can_delete=False,
                                    max_num=None):
    """Return a FormSet for the given form class."""

    # Here is the version checking and max_num fixing
    # Django Ticket: 13023
    import django
    if django.VERSION[0] == 1 and django.VERSION[1] >= 2 \
            or django.VERSION[0] > 1:
        #apply the max_num fix.
        if max_num == 0:
            max_num = None

    attrs = {'form': form, 'extra': extra,
             'can_order': can_order, 'can_delete': can_delete,
             'max_num': max_num}
    return type(form.__name__ + 'FormSet', (formset,), attrs)
