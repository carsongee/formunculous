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
"""
This provides the views for creating forms in formunculous.
"""
import datetime

from django import http
from django import template
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory
from django.shortcuts import (get_object_or_404,
                              render_to_response,
                              get_list_or_404,
                              redirect
                          )
from django.views.generic.base import TemplateView
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from formunculous.forms import *
from formunculous.mixins import ChangeFormMixin, AddFormMixin, DeleteFormMixin
from formunculous.models import *
from formunculous.utils import build_template_structure
# Used for getting classes as attributes for field classes.
import formunculous.models as funcmodels


class Index(ChangeFormMixin, TemplateView):
    """
       Lists available applications, links to create/copy/delete/modify
       application definitions.
    """

    http_method_names = ['get', ]
    template_name = 'formunculous/builder_index.html'

    def get_context_data(self, **kwargs):
        """
        Sort application definition objects based on what is selected, 
        default to alphabetical by Name.
        """
        context = super(self.__class__, self).get_context_data(**kwargs)
        s = "name"
        if "s" in self.request.GET:
            s = self.request.GET['s']
            if s.lstrip('-') not in ["name", "owner", "start_date", "stop_date",]:
                s = "name"

        app_defs = ApplicationDefinition.objects.filter(parent=None).order_by(s)
        context['app_defs'] = app_defs
        context['s'] = s
        return context


class AddAppDef(AddFormMixin, TemplateView):
    """
       Creates an application definition with the required fields.
    """

    http_method_names = ['get', 'post', ]
    template_name = 'formunculous/builder_ad_form.html'
    form = None

    def post(self, request, *args, **kwargs):
        """Handle post to add a new application definition."""

        if (request.POST.has_key('finish')
            or request.POST.has_key('add_another')\
            or request.POST.has_key('edit')\
            or request.POST.has_key('form')):

            self.form = ApplicationDefinitionForm(request.POST)
            if self.form.is_valid():
                self.form.save()
                if request.POST.has_key('finish'):
                    return redirect('builder-index')
                elif request.POST.has_key('add_another'):
                    return redirect('builder-add-ad')
                elif request.POST.has_key('edit'):
                    return redirect('builder-edit-ad', slug=self.form.instance.slug)
                elif request.POST.has_key('form'):
                    return redirect('builder-edit-fields',
                                    slug=self.form.instance.slug)
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Provide context data to handle new form, or show form errors"""
        context = super(self.__class__, self).get_context_data(**kwargs)

        breadcrumbs = [{'name': _('Builder Index'), 
                        'url': reverse('builder-index')},]
        if not self.form:
            self.form = ApplicationDefinitionForm()

        context['form'] = self.form
        context['breadcrumbs'] = breadcrumbs
        context['add'] = True
        return context


class ModifyAppDef(ChangeFormMixin, TemplateView):
    """
       Modifies an existing application defintion
    """

    http_method_names = ['get', 'post', ]
    template_name = 'formunculous/builder_ad_form.html'
    form = None

    def set_ad(self, slug):
        """
        Check that we have a valid application
        definition and dump out if not
        """
        self.ad = get_object_or_404(ApplicationDefinition, slug=slug)
        if self.ad.parent:
            raise http.Http404, _('You cannot edit a sub-form definition directly')

    def post(self, request, *args, **kwargs):
        """Handle application definition modification request"""
   
        self.set_ad(kwargs['slug'])
        if (request.POST.has_key('finish') or
            request.POST.has_key('edit') or
            request.POST.has_key('form')):
         
            self.form = ApplicationDefinitionForm(request.POST, instance=self.ad)
            if self.form.is_valid():
                self.form.save()
                if request.POST.has_key('finish'):
                    return redirect('builder-index')
                elif request.POST.has_key('form'):
                    return redirect('builder-edit-fields',
                                    slug=self.form.instance.slug)
                elif request.POST.has_key('edit'):
                    return redirect('builder-edit-ad', slug=self.form.instance.slug)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        self.set_ad(kwargs['slug'])

        breadcrumbs = [{'name': _('Builder Index'), 
                    'url': reverse('builder-index')},]
        if not self.form:
            self.form = ApplicationDefinitionForm(instance=self.ad)

        context['breadcrumbs'] = breadcrumbs
        context['form'] = self.form
        context['ad'] = self.ad
        context['add'] = False
        return context


class CopyAppDef(ChangeFormMixin, TemplateView):
    """
       Creates a copy of an existing application and gives it a new slug.
       Upon creation, redirects the user to edit the base application
       definition. Fired from AJAX POST form, so ignoring get and rendering
       on post.
    """

    http_method_names = ['post', ]
    template_name = 'formunculous/ajax_copy_ad.html'
    ad = None

    def post(self, request, *args, **kwargs):

        if request.POST.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition,
                                   id=int(request.POST['ad']))
            ad_id = ad.id
            new_name = request.POST['name']
            new_slug = request.POST['slug']
            # Get field definition set for duplication
            field_definitions = ad.fielddefinition_set.all()

            # Set new parameters for the duped AD
            # Nuke the pk so a new one is created
            # Set the sites and reviewers.

            ad.name = new_name
            ad.slug = new_slug
            ad.id = None
            ad.save()
            
            old_ad = ApplicationDefinition.objects.get(id=ad_id)
            for site in old_ad.sites.all():
                ad.sites.add(site)

            for reviewer in old_ad.reviewers.all():
                ad.reviewers.add(reviewer)

            # Loop through the fields and dupe them to point to the new AD
            for fd in field_definitions:
                # Find any dropdown definitions for later copying
                dropdowns = DropDownChoices.objects.filter(field_definition=fd)

                fd.id = None
                fd.application = ad
                fd.save()

                for dd in dropdowns:
                    dd.id = None
                    dd.field_definition = fd
                    dd.save()

            # Do it all again for sub_apps, should do tail recursion, but it is
            # only one level deep.
            sub_ads = ApplicationDefinition.objects.filter(parent__id=ad_id)
            for sub_ad in sub_ads:
                new_sub_slug = "%s_%s" % (new_slug, sub_ad.slug)
                field_definitions = sub_ad.fielddefinition_set.all()
                sub_app_def = SubApplicationDefinition.objects.get(
                    app_definition=sub_ad
                )
                sub_ad.slug = new_sub_slug
                sub_ad.id = None
                sub_ad.parent = ad
                sub_ad.save()
                sub_app_def.id = None
                sub_app_def.app_definition = sub_ad
                sub_app_def.save()

                for fd in field_definitions:
                    dropdowns = DropDownChoices.objects.filter(
                        field_definition=fd)

                    fd.id = None
                    fd.application = sub_ad
                    fd.save()

                    for dd in dropdowns:
                        dd.id = None
                        dd.field_definition = fd
                        dd.save()
            self.ad = ad
            return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Return context, but only if it exists, raise 404 otherwise"""
        context = super(self.__class__, self).get_context_data(**kwargs)

        if self.ad:
            context['ad'] = self.ad
        else:
            raise http.Http404
        return context


class DeleteAppDef(DeleteFormMixin, TemplateView):
    """
       Deletes an application definition and the applications/data
       associated with them (ala admin delete).
    """
    http_method_names = ['post', ]
    template_name = 'formunculous/ajax_delete_ad.html'

    def post(self, request, *args, **kwargs):

        if request.POST.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition,
                                   id=int(request.POST['ad']))
            self.name = ad.name
            ad.delete()
        else:
            raise http.Http404, _('Form Definition does not exist')
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        if not self.name:
            raise http.Http404, _('Form Definition does not exist')
        context['name'] = self.name
        return context

class PreviewAppDef(ChangeFormMixin, TemplateView):
    """
       This renders the application definition form
       without creating submit buttons
    """

    http_method_names = ['get', ]

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        if self.request.GET.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition,
                                   id=int(self.request.GET['ad']))
        else:
            raise http.Http404, _('Form Definition does not exist')

        form = ApplicationForm(ad)
        # create structure for the template that looks like
        # form-> (group, pre-text, post-text, page)
        fields = []
        for field in ad.fielddefinition_set.filter(reviewer_only=False):
            field_dict = {'group': field.group, 
                          'pre_text': mark_safe(field.pre_text), 
                          'post_text': mark_safe(field.post_text),
                          'field': form.__getitem__(field.slug),},
            fields += field_dict

        # Build sub forms based on sub application definitions
        subforms = []
        if ad.applicationdefinition_set.all():
            sub_apps = ad.applicationdefinition_set.all()
            for sub_app in sub_apps:
                sub_ad = sub_app.subapplicationdefinition_set.get()
                sub_app_formset = formunculous_subformset_factory(ApplicationForm,
                                                  formset=FormunculousBaseFormSet,
                                                  extra=sub_ad.extras,
                                                  max_num=sub_ad.max_entries)
                formset = sub_app_formset(app_def=sub_app,
                                                prefix=sub_app.slug)
                forms = []
                for sub_form in formset.forms:
                    forms.append({"form": sub_form,
                                  "fields": build_template_structure(sub_form,
                                                                     sub_app)
                                  })
                subforms.append({ "sub_ad": sub_app, "forms": forms,
                                  "formset": formset})
        
        # Try a customized template.
        # if it is there use it, else use the default template.
        try:
            self.template_name = template.loader.get_template(
                'formunculous/{0}/apply.html'.format(ad.slug))
        except:
            self.template_name = 'formunculous/apply.html'

        context['form'] = form
        context['ad'] = ad
        context['fields'] = fields
        context['subforms'] = subforms
        context['preview'] = True

        return context


class ModifyFields(ChangeFormMixin, TemplateView):
    """
       This is the main page for creating/editing the field definitions
       for a specific application definition.  It handles the form processing,
       but other views will handle additions/previews/deletions to the
       main form.
    """

    http_method_names = ['get', 'post', ]
    template_name = 'formunculous/builder_edit_fields.html'
    formset = None

    def set_models(self, slug):

        self.ad = get_object_or_404(ApplicationDefinition, slug=slug)

        # Figure out whether this is a parent and can have subforms or not
        # Formunculous only allows one level of subapps.
        if self.ad.parent:
            self.is_parent = False
        else:
            self.is_parent = True

        self.FieldDefinitionFormSet = inlineformset_factory(
            ApplicationDefinition, 
            FieldDefinition, 
            extra=0,
            form=FieldDefinitionForm
        )
        
    def post(self, request, *args, **kwargs): 

        self.set_models(kwargs['slug'])
        self.formset = self.FieldDefinitionFormSet(
            self.request.POST,
            instance=self.ad
        )
        if self.formset.is_valid():
            instances = self.formset.save()
            if self.request.POST.has_key('finish'):
                return redirect('builder-index')
            elif self.request.POST.has_key('edit'):
                return redirect('builder-edit-fields', slug=kwargs['slug'])

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        self.set_models(kwargs['slug'])

        breadcrumbs = [{'name': _('Builder Index'), 
                        'url': reverse('builder-index')},]
        if not self.is_parent:
            breadcrumbs.append(
                {'name': '%s' % ad.parent.name, 
                 'url': reverse('builder-edit-fields', 
                                kwargs={'slug': ad.parent.slug})
             })

        # Should probably pass in a widget with sample label in with this
        # to provide a tiny preview.
        field_types = []
        for type in FieldDefinition.field_types:

            # Get the icon url from media root from the field
            # class if the class exists and has an icon defined.
            field_icon = None
            if hasattr(funcmodels, type[0]):
                field_class = getattr(funcmodels, type[0])
                if hasattr(field_class, 'icon'):
                    field_icon = field_class.icon

            field_types.append({'type': type[0], 
                                'name': type[1],
                                'icon': field_icon,
                                })
        if not self.formset:
            self.formset = self.FieldDefinitionFormSet(instance=self.ad)

        context['breadcrumbs'] = breadcrumbs
        context['ad'] = self.ad
        context['formset'] = self.formset
        context['is_parent'] = self.is_parent
        context['field_types'] = field_types
        return context


class AddFieldForm(ChangeFormMixin, TemplateView):
    """
       Returns a new fielddef form instance for inclusion in the main
       pages formset.  It builds a formset with 1 extra form and renders
       that form to html for an AJAX grab.  The JS on the
    """

    http_method_names = ['get', ]
    template_name = 'formunculous/includes/fd_fields.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        ad = get_object_or_404(ApplicationDefinition, slug=kwargs['slug'])

        FieldDefinitionFormSet = inlineformset_factory(
            ApplicationDefinition,
            FieldDefinition, 
            extra=4,
            form=FieldDefinitionForm
        )
        formset = FieldDefinitionFormSet(instance=ad)

        extra_form = formset.forms[-1]

        context['form'] = extra_form
        return context

class AddModifyDropDown(ChangeFormMixin, TemplateView):
    """
       Manages the dropdown choices for a field
    """

    http_method_names = ['get', 'post', ]
    template_name = 'formunculous/builder_dropdown.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        if self.request.GET.has_key('id'):
            id = self.request.GET['id']
        else:
            raise http.Http404, _('No Field Definition Specified')        

        fd = get_object_or_404(FieldDefinition, id=int(id))

        DropDownFormSet = inlineformset_factory(
            FieldDefinition,
            DropDownChoices,
            extra=3
        )

        if self.request.method == 'POST':
            formset = DropDownFormSet(self.request.POST, 
                                      instance=fd)
            if formset.is_valid():
                instances = formset.save()
                formset = DropDownFormSet(instance=fd)
        else:
            formset = DropDownFormSet(instance=fd)
        
        context['formset'] = formset
        context['fd'] = fd
        return context


class AddSubAppDef(ChangeFormMixin, TemplateView):
    """
       This creates a sub-form for the defined application definition.
       It creates a new instance of an ApplicationDefinition with
       its parent pointed at the parent AppDef, and then creates
       a sub_app_def to hold the sub form specific information.
    """

    http_method_names = ['post', ]
    template_name = 'formunculous/ajax_add_subform.html'

    def post(self, request, *args, **kwargs):

        if request.POST.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition, 
                                   id=int(request.POST['ad']))
            name = request.POST['name']
            slug = request.POST['slug']
            min_entries = int(request.POST['min_entries'])
            max_entries = int(request.POST['max_entries'])
            extras = int(request.POST['extras'])

            if min_entries > max_entries and max_entries != 0:
                raise http.Http500(_("Minimum entries cannot be greater than\
                                       max entries"))


            # Create new application definition pointed
            # at the one defined in AD
            child_ad = ApplicationDefinition(
                parent=ad, owner=ad.owner,
                notify_owner=False, slug=slug,
                description='', name=name,
                start_date=datetime.datetime(1970, 1, 1, 0, 0),
                stop_date=datetime.datetime(datetime.MAXYEAR, 1, 1, 0, 0),
                authentication=False, authentication_multi_submit=False,
                notify_reviewers=False, email_only=False
            )
            child_ad.save()
            self.sub_ad = SubApplicationDefinition(
                app_definition=child_ad,
                min_entries=min_entries,
                max_entries=max_entries,
                extras=extras
            )
            self.sub_ad.save()

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        if self.sub_ad:
            context['subform'] = self.sub_ad
        else:
            raise http.Http404
        return context


class ChangeSubAppDef(ChangeFormMixin, TemplateView):
    """
    This allows changing of the attributes for a subapp.  It grabs the
    subapp definition out of the request string, modifies and saves the
    fields that were submitted.
    """

    http_method_names = ['post', ]
    template_name = 'formunculous/ajax_add_subform.html'

    def post(self, request, *args, **kwargs):
    
        if request.POST.has_key('sad'):
            child_ad = get_object_or_404(ApplicationDefinition, 
                                   id=int(request.POST['sad']))

            name = request.POST['name']
            slug = request.POST['slug']
            min_entries = int(request.POST['min_entries'])
            max_entries = int(request.POST['max_entries'])
            extras = int(request.POST['extras'])

            if min_entries > max_entries and max_entries != 0:
                raise http.Http500(_("Minimum entries cannot be greater than\
                                       max entries"))
                
            # Get the SubApplicationDefinition for the app_def
            # if it has more than one or two, than let the exception
            # occur, since we are using a limited AJAX call to post
            # here.
            self.sub_ad = child_ad.subapplicationdefinition_set.get()

            self.sub_ad.min_entries = min_entries
            self.sub_ad.max_entries = max_entries
            self.sub_ad.extras = extras
            self.sub_ad.save()

            child_ad.name = name
            child_ad.slug = slug
            child_ad.save()

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        # Reusing the add_subform template because the rendered HTML is the same
        # for changing as it is for adding, but the javascript will replace
        # the existing tr with the rendered template instead of appending it.
        if self.sub_ad:
            context['subform'] = self.sub_ad
        else:
            raise http.Http404
        return context
