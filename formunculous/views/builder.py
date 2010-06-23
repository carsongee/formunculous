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

from formunculous.models import *
from formunculous.utils import build_template_structure
from django.forms.formsets import formset_factory
from django import http
from formunculous.forms import *
from django import template
from django.shortcuts import get_object_or_404, render_to_response, get_list_or_404, redirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.contrib.auth.decorators import permission_required


import datetime

# These are the views for building forms.  This part of the site should
# be disconnected ala an admin site.

def index(request):
    """
       Lists available applications, links to create/copy/delete/modify
       application definitions.
    """

    # Sort application definition objects based on what is selected, default
    # to alphabetical by Name.
    s = "name"
    if "s" in request.GET:
        s = request.GET['s']
        if s.lstrip('-') not in ["name", "owner", "start_date", "stop_date",]:
            s = "name"

    app_defs = ApplicationDefinition.objects.filter(parent=None).order_by(s)

    return render_to_response('formunculous/builder_index.html',
                              {'app_defs': app_defs, 's': s},
                              context_instance=template.RequestContext(request))


index = permission_required('formunculous.change_form')(index)

def add_app_def(request):

    """
       Creates an application definition with the required fields.
    """

    form = None

    breadcrumbs = [{'name': _('Builder Index'), 
                    'url': reverse('builder-index')},]
    if request.method == 'POST':
        if request.POST.has_key('finish')\
                or request.POST.has_key('add_another')\
                or request.POST.has_key('edit')\
                or request.POST.has_key('form'):

            form = ApplicationDefinitionForm(request.POST)
            if form.is_valid():
                form.save()
                if request.POST.has_key('finish'):
                    return redirect('builder-index')
                elif request.POST.has_key('add_another'):
                    return redirect('builder-add-ad')
                elif request.POST.has_key('edit'):
                    return redirect('builder-edit-ad', slug=form.instance.slug)
                elif request.POST.has_key('form'):
                    return redirect('builder-edit-fields',
                                    slug = form.instance.slug)

    if not form:
        form = ApplicationDefinitionForm()

    return render_to_response('formunculous/builder_ad_form.html',
                              {'form': form, 'add': True,
                               'breadcrumbs': breadcrumbs, },
                              context_instance=template.RequestContext(request))

add_app_def = permission_required('formunculous.add_form')(add_app_def)

def modify_app_def(request, slug):

    """
       Modifies an existing application defintion
    """

    breadcrumbs = [{'name': _('Builder Index'), 
                    'url': reverse('builder-index')},]

    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    if ad.parent:
        raise http.Http404, _('You cannot edit a sub-form definition directly')
    
    form = None
    
    if request.method == 'POST':
        if request.POST.has_key('finish') or request.POST.has_key('edit') or \
                request.POST.has_key('form'):
            form = ApplicationDefinitionForm(request.POST, instance = ad)
            if form.is_valid():
                form.save()
                if request.POST.has_key('finish'):
                    return redirect('builder-index')
                elif request.POST.has_key('form'):
                    return redirect('builder-edit-fields',
                                    slug=form.instance.slug)
                elif request.POST.has_key('edit'):
                    return redirect('builder-edit-ad', slug=form.instance.slug)
    if not form:
        form = ApplicationDefinitionForm(instance = ad)

    return render_to_response('formunculous/builder_ad_form.html',
                              {'form': form, 'ad': ad,
                               'breadcrumbs': breadcrumbs, },
                              context_instance=template.RequestContext(request))

modify_app_def = permission_required('formunculous.change_form')(modify_app_def)

def copy_app_def(request):

    """
       Creates a copy of an existing application and gives it a new slug.
       Upon creation, redirects the user to edit the base application
       definition.
    """
    if request.method == 'POST':
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
                dropdowns = DropDownChoices.objects.filter(field_definition = fd)

                fd.id = None
                fd.application = ad
                fd.save()

                for dd in dropdowns:
                    dd.id = None
                    dd.field_definition = fd
                    dd.save()

            # Do it all again for sub_apps, should do tail recursion, but it is
            # only one level deep.
            sub_ads = ApplicationDefinition.objects.filter(parent__id = ad_id)
            for sub_ad in sub_ads:
                new_sub_slug = "%s_%s" % (new_slug, sub_ad.slug)
                field_definitions = sub_ad.fielddefinition_set.all()
                sub_app_def = SubApplicationDefinition.objects.get(app_definition=sub_ad)
                
                sub_ad.slug = new_sub_slug
                sub_ad.id = None
                sub_ad.parent = ad

                sub_ad.save()

                sub_app_def.id = None
                sub_app_def.app_definition = sub_ad
                sub_app_def.save()

                for fd in field_definitions:
                    dropdowns = DropDownChoices.objects.filter(field_definition = fd)

                    fd.id = None
                    fd.application = sub_ad
                    fd.save()

                    for dd in dropdowns:
                        dd.id = None
                        dd.field_definition = fd
                        dd.save()

    return render_to_response('formunculous/ajax_copy_ad.html',
                              { 'ad': ad,},
                              context_instance=template.RequestContext(request))

copy_app_def = permission_required('formunculous.change_form')(copy_app_def)

def delete_app_def(request):

    """
       Deletes an application definition and the applications/data
       associated with them (ala admin delete).
    """

    if request.method == 'POST':
        if request.POST.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition,
                                   id=int(request.POST['ad']))
            name = ad.name
            ad.delete()
        else:
            raise http.Http404, _('Form Definition does not exist')
    else:
        raise http.Http404, _('Form Definition does not exist')

    return render_to_response('formunculous/ajax_delete_ad.html',
                              {'name': name,},
                              context_instance=template.RequestContext(request))
delete_app_def = permission_required('formunculous.delete_form')(delete_app_def)

def preview_app_def(request):
    """
       This renders the application definition form
       without creating submit buttons
    """
    if request.method == 'GET':
        if request.GET.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition,
                                   id=int(request.GET['ad']))
        else:
            raise http.Http404, _('Form Definition does not exist')
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
                                              max_num = sub_ad.max_entries)
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
        t = template.loader.get_template('formunculous/%s/apply.html' % ad.slug)
        t = 'formunculous/%s/apply.html' % ad.slug
    except:
        t = 'formunculous/apply.html'

    return render_to_response('formunculous/apply.html',
                              {'form': form, 'ad': ad, 'fields': fields,
                               'subforms': subforms, 'preview': True,},
                              context_instance=template.RequestContext(request))

preview_app_def = permission_required('formunculous.change_form')(preview_app_def)

def modify_fields(request, slug):

    """
       This is the main page for creating/editing the field definitions
       for a specific application definition.  It handles the form processing,
       but other views will handle additions/previews/deletions to the
       main form.
    """

    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    
    # Figure out whether this is a parent and can have subforms or not
    # Formunculous only allows one level of subapps.
    if ad.parent:
        is_parent = False
    else:
        is_parent = True

    FieldDefinitionFormSet = inlineformset_factory(ApplicationDefinition, 
                                                   FieldDefinition, 
                                                   extra=0,
                                                   form=FieldDefinitionForm)

    breadcrumbs = [{'name': _('Builder Index'), 
                    'url': reverse('builder-index')},]
    if not is_parent:
        breadcrumbs.append({'name': '%s' % ad.parent.name, 
                             'url': reverse('builder-edit-fields', 
                                            kwargs=
                                            {'slug': ad.parent.slug}
                                            )
                            })

    # Should probably pass in a widget with sample label in with this
    # to provide a tiny preview.
    field_types = []
    for type in FieldDefinition.field_types:
        field_types.append({'type': type[0], 'name': type[1],})

    if request.method == 'POST':
        formset = FieldDefinitionFormSet(request.POST, 
                                         instance=ad)
        if formset.is_valid():
            instances = formset.save()
        
            if request.POST.has_key('finish'):
                return redirect('builder-index')
            elif request.POST.has_key('edit'):
                return redirect('builder-edit-fields', slug = slug)
    else:
        formset = FieldDefinitionFormSet(instance=ad)

    return render_to_response('formunculous/builder_edit_fields.html',
                              {'ad': ad, 'formset': formset,
                               'breadcrumbs': breadcrumbs, 
                               'is_parent': is_parent,
                               'field_types': field_types},
                              context_instance=template.RequestContext(request))

modify_fields = permission_required('formunculous.change_form')(modify_fields)

def add_field_form(request, slug):

    """
       Returns a new fielddef form instance for inclusion in the main
       pages formset.  It builds a formset with 1 extra form and renders
       that form to html for an AJAX grab.  The JS on the
    """
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    FieldDefinitionFormSet = inlineformset_factory(ApplicationDefinition,
                                                   FieldDefinition, 
                                                   extra=4,
                                                   form=FieldDefinitionForm)

    formset = FieldDefinitionFormSet(instance=ad)

    extra_form = formset.forms[-1]

    return render_to_response('formunculous/includes/fd_fields.html',
                              { 'form': extra_form, },
                              context_instance=template.RequestContext(request))

add_field_form = permission_required('formunculous.change_form')(add_field_form)

def add_modify_dropdown(request):

    """
       Manages the dropdown choices for a field
    """

    if request.GET.has_key('id'):
        id = request.GET['id']
    else:
        raise http.Http404, _('No Field Definition Specified')        
    
    fd = get_object_or_404(FieldDefinition, id=int(id))

    DropDownFormSet = inlineformset_factory(FieldDefinition, DropDownChoices,
                                            extra=3)
    
    if request.method == 'POST':
        formset = DropDownFormSet(request.POST, 
                                         instance=fd)
        if formset.is_valid():
            instances = formset.save()
            formset = DropDownFormSet(instance=fd)
    else:
        formset = DropDownFormSet(instance=fd)

    return render_to_response('formunculous/builder_dropdown.html',
                              {'formset': formset, 'fd': fd, },
                              context_instance=template.RequestContext(request))
add_modify_dropdown = permission_required('formunculous.change_form')(add_modify_dropdown)



def add_subapp_def(request):

    """
       This creates a sub-form for the defined application definition.
       It creates a new instance of an ApplicationDefinition with
       its parent pointed at the parent AppDef, and then creates
       a sub_app_def to hold the sub form specific information.
    """

    if request.method == 'POST':
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
            child_ad = ApplicationDefinition(parent = ad, owner = ad.owner,
                                             notify_owner = False, slug = slug,
                                             description = '',
                                             name = name,
                                             start_date = datetime.datetime(2010, 1, 1, 0, 0),
                                             stop_date = datetime.datetime(datetime.MAXYEAR, 1, 1, 0, 0),
                                             authentication = False,
                                             authentication_multi_submit = False,
                                             notify_reviewers = False,
                                             email_only = False)
            child_ad.save()
            sub_ad = SubApplicationDefinition(app_definition = child_ad,
                                              min_entries = min_entries,
                                              max_entries = max_entries,
                                              extras = extras)
            sub_ad.save()

    return render_to_response('formunculous/ajax_add_subform.html',
                              {'subform': sub_ad, },
                              context_instance=template.RequestContext(request))

add_subapp_def = permission_required('formunculous.change_form')(add_subapp_def)

def change_subapp_def(request):

    """
    This allows changing of the attributes for a subapp.  It grabs the
    subapp definition out of the request string, modifies and saves the
    fields that were submitted.
    """
    if request.method == 'POST':
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
            sub_ad = child_ad.subapplicationdefinition_set.get()

            sub_ad.min_entries = min_entries
            sub_ad.max_entries = max_entries
            sub_ad.extras = extras
            sub_ad.save()

            child_ad.name = name
            child_ad.slug = slug
            child_ad.save()

    # Reusing the add_subform template because the rendered HTML is the same
    # for changing as it is for adding, but the javascript will replace
    # the existing tr with the rendered template instead of appending it.
    return render_to_response('formunculous/ajax_add_subform.html',
                              {'subform': sub_ad, },
                              context_instance=template.RequestContext(request))


change_subapp_def = permission_required('formunculous.change_form')(change_subapp_def)
