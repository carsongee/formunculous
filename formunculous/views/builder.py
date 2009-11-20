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


from formunculous.models import *
from django import http
from formunculous.forms import *
from django import template
from django.shortcuts import get_object_or_404, redirect, render_to_response, get_list_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.contrib.auth.decorators import permission_required

# These are the views for building forms.  This part of the site should
# be disconnected ala an admin site.

def index(request):
    """
       Lists available applications, links to create/copy/delete/modify
       application definitions.
    """
    app_defs = ApplicationDefinition.objects.all()

    return render_to_response('formunculous/builder_index.html',
                              {'app_defs': app_defs,},
                              context_instance=template.RequestContext(request))


index = permission_required('formunculous.can_edit_forms')(index)

def add_app_def(request):

    """
       Creates an application definition with the required fields.
    """

    form = None

    breadcrumbs = [{'name': _('Builder Index'), 'url': reverse('builder-index')},]
    if request.method == 'POST':
        if request.POST.has_key('finish') or request.POST.has_key('add_another')\
                or request.POST.has_key('edit') or request.POST.has_key('form'):
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
                    return redirect('builder-edit-fields', slug = form.instance.slug)

    if not form:
        form = ApplicationDefinitionForm()

    return render_to_response('formunculous/builder_ad_form.html',
                              {'form': form, 'add': True,
                               'breadcrumbs': breadcrumbs, },
                              context_instance=template.RequestContext(request))

add_app_def = permission_required('formunculous.can_edit_forms')(add_app_def)

def modify_app_def(request, slug):

    """
       Modifies an existing application defintion
    """

    breadcrumbs = [{'name': _('Builder Index'), 'url': reverse('builder-index')},]

    ad = get_object_or_404(ApplicationDefinition, slug=slug)
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
                    return redirect('builder-edit-fields', slug=form.instance.slug)
                elif request.POST.has_key('edit'):
                    return redirect('builder-edit-ad', slug=form.instance.slug)
    if not form:
        form = ApplicationDefinitionForm(instance = ad)

    return render_to_response('formunculous/builder_ad_form.html',
                              {'form': form,
                               'breadcrumbs': breadcrumbs, },
                              context_instance=template.RequestContext(request))

modify_app_def = permission_required('formunculous.can_edit_forms')(modify_app_def)

def copy_app_def(request):

    """
       Creates a copy of an existing application and gives it a new slug.
       Upon creation, redirects the user to edit the base application
       definition.
    """
    if request.method == 'POST':
        if request.POST.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition, id=int(request.POST['ad']))
            new_name = request.POST['name']
            new_slug = request.POST['slug']
            # Get field definition set for duplication
            field_definitions = ad.fielddefinition_set.all()
            # Set new parameters for the duped AD, nuke the pk, so a new one is created
            ad.name = new_name
            ad.slug = new_slug
            ad.id = None
            ad.save()
            # Loop through the fields and dupe them to point to the new AD
            for fd in field_definitions:
                fd.id = None
                fd.application = ad
                fd.save()

    return render_to_response('formunculous/ajax_copy_ad.html',
                              { 'ad': ad,},
                              context_instance=template.RequestContext(request))

copy_app_def = permission_required('formunculous.can_edit_forms')(copy_app_def)

def delete_app_def(request):

    """
       Deletes an application definition and the applications/data
       associated with them (ala admin delete).
    """

    if request.method == 'POST':
        if request.POST.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition, id=int(request.POST['ad']))
            name = ad.name
            ad.delete()
        else:
            raise http.Http404, _('Application Defintion does not exist')
    else:
        raise http.Http404, _('Application Defintion does not exist')

    return render_to_response('formunculous/ajax_delete_ad.html',
                              {'name': name,},
                              context_instance=template.RequestContext(request))
delete_app_def = permission_required('formunculous.can_edit_forms')(delete_app_def)

def preview_app_def(request):
    """
       This renders the application definition form
       without creating submit buttons
    """
    if request.method == 'GET':
        if request.GET.has_key('ad'):
            ad = get_object_or_404(ApplicationDefinition, id=int(request.GET['ad']))
        else:
            raise http.Http404, _('Application Defintion does not exist')
    else:
        raise http.Http404, _('Application Defintion does not exist')
    
    form = ApplicationForm(ad)
    # create structure for the template that looks like
    # form-> (group, pre-text, post-text, page)
    fields = []
    for field in ad.fielddefinition_set.filter(reviewer_only=False):
        field_dict = {'group': field.group, 'pre_text': mark_safe(field.pre_text), 
                      'post_text': mark_safe(field.post_text),
                      'field': form.__getitem__(field.slug),},
        fields += field_dict    
        
    # Try a customized template.
    # if it is there use it, else use the default template.
    try:
        t = template.loader.get_template('formunculous/%s/apply.html' % ad.slug)
        t = 'formunculous/%s/apply.html' % ad.slug
    except:
        t = 'formunculous/apply.html'

    return render_to_response('formunculous/apply.html',
                              {'form': form, 'ad': ad, 'fields': fields,},
                              context_instance=template.RequestContext(request))

preview_app_def = permission_required('formunculous.can_edit_forms')(preview_app_def)

def modify_fields(request, slug):

    """
       This is the main page for creating/editing the field definitions
       for a specific application definition.  It handles the form processing,
       but other views will handle additions/previews/deletions to the
       main form.
    """

    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    FieldDefinitionFormSet = inlineformset_factory(ApplicationDefinition, FieldDefinition, 
                                                  extra=0, form=FieldDefinitionForm)

    breadcrumbs = [{'name': _('Builder Index'), 'url': reverse('builder-index')},]

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
                               'field_types': field_types},
                              context_instance=template.RequestContext(request))

modify_fields = permission_required('formunculous.can_edit_forms')(modify_fields)

def add_field_form(request, slug):

    """
       Returns a new fielddef form instance for inclusion in the main
       pages formset.  It builds a formset with 1 extra form and renders
       that form to html for an AJAX grab.  The JS on the
    """
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    FieldDefinitionFormSet = inlineformset_factory(ApplicationDefinition, FieldDefinition, 
                                                  extra=4, form=FieldDefinitionForm)

    formset = FieldDefinitionFormSet(instance=ad)

    extra_form = formset.forms[-1]

    return render_to_response('formunculous/includes/fd_fields.html',
                              { 'form': extra_form, },
                              context_instance=template.RequestContext(request))

add_field_form = permission_required('formunculous.can_edit_forms')(add_field_form)

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
add_modify_dropdown = permission_required('formunculous.can_edit_forms')(add_modify_dropdown)
