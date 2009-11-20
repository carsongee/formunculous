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
from formunculous.forms import *
from django.conf import settings
from django import template
from django.shortcuts import get_object_or_404, redirect, render_to_response, get_list_or_404
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

def index(request, slug):
    """
       This shows all the completed applications for an application definition given
       by the slug.  The application definition index is provided in the apply view
       module.
    """
    
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    breadcrumbs = [{'url': reverse('formunculous-index'), 'name': _('Applications')},]

    # Check if they are authorized to view this page.
    validation = validate_user(request, ad)
    if validation:
        return validation
        
    apps = Application.objects.filter(app_definition = ad).exclude(submission_date=None)
    header_fields = ad.fielddefinition_set.filter(header=True)

    # By default sort on date, since that is the only column I know
    # will be displayed
    column = 0

    reverse_sort = False
    if "s" in request.GET:
        sort_column = request.GET['s']
        if sort_column[0] == '-':
            reverse_sort = True
            sort_column = sort_column.lstrip('-')
        try:
            column = int(sort_column)
        except:
            pass

    headers = []
    i = 0
    for header in header_fields:
        if column == i and not reverse_sort:
            sort = '-%s' % i
        else:
            sort = i
        header_dict = {'name': mark_safe(header.label), 'url': '%s?s=%s' % (reverse('reviewer-index', kwargs={'slug':slug}), sort),},
        headers += header_dict
        i+=1

    # Add on submission date
    if column == i and not reverse_sort:
        sort = '-%s' % i
    else:
        sort = i
    headers.append({'name': _('Submission Date and Time'),
                    'url': '%s?s=%s' % (reverse('reviewer-index', kwargs={'slug':slug}), sort),}
                   )

    value_table = []
    for app in apps:
        value_row = []
        for field in header_fields:
            # Fill with URL for detailed app view
            value_row.append({'value': app.get_field_value(field.slug),
                             'url': reverse('reviewer-application', 
                                            kwargs={'slug': slug,
                                                    'app': app.id,})},)
        # Add the submission date to the end of the row
        value_row.append({'value': app.submission_date, 
                          'url': reverse('reviewer-application', 
                                         kwargs={'slug': slug,
                                                 'app': app.id,}),
                         'id': app.id,})
        value_table.append(value_row)

    # Sort based on column of the outputted table, because we are pulling
    # data from so many different places, it would be nearly impossible
    # to sort from the DB.

    def header_sorter(x, y):
        return cmp(x[column]['value'], y[column]['value'])

    value_table.sort(header_sorter)

    if reverse_sort:
        value_table.reverse()

    return render_to_response('formunculous/review_index.html',
                              { 'ad': ad, 'apps': apps,
                                'headers': headers,
                                'data': value_table,
                                'breadcrumbs': breadcrumbs},
                              context_instance=template.RequestContext(request))


def application(request, slug, app):

    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    app = get_object_or_404(Application, id=app)

    validation = validate_user(request, ad)
    if validation:
        return validation


    breadcrumbs = [{'url': reverse('formunculous-index'), 'name': _('Application Index')},
                   {'url': reverse('reviewer-index', kwargs={'slug': slug}), 'name':  ad.name},
                  ]

    if request.method == 'POST':
        if request.POST.has_key('save'):
            rev_form = ApplicationForm(ad, app, True, request.POST, request.FILES)
            if rev_form.is_valid():
                rev_form.save()
                return redirect("reviewer-application", slug=slug, app=app.id)



    rev_form = ApplicationForm(ad, app, True)
    # create structure for the template that looks like
    # form-> (group, pre-text, post-text, page)
    fields = []
    for field in ad.fielddefinition_set.filter(reviewer_only=True):
        field_dict = {'group': field.group, 'pre_text': mark_safe(field.pre_text), 
                      'post_text': mark_safe(field.post_text),
                      'field': rev_form.__getitem__(field.slug),},
        fields += field_dict
    
    
    return render_to_response('formunculous/review_application.html',
                              {'ad': ad, 'app': app,
                               'app_fields': app.get_field_values(),
                               'review_form': rev_form, 'fields': fields, 
                               'breadcrumbs': breadcrumbs, },
                              context_instance=template.RequestContext(request))

def delete(request, slug):

    if request.method == 'POST':
        if request.POST.has_key('id'):
            app = get_object_or_404(Application, id=int(request.POST['id']))
            validation = validate_user(request, app.app_definition)
            if validation:
                return validation
            app.delete()
        else:
            raise Http404, _('Application does not exit')

    return HttpResponse(_('Application Successfully Delete'))
    

def validate_user(request, ad):
    # Check if they are authorized to view this page.
    if not (request.user.is_authenticated() \
                and request.user in ad.reviewers.all()):
        return render_to_response('formunculous/denied.html',
                                  context_instance=template.RequestContext(request))
    else:
        return None
        
