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
#     Copyright 2009, 2010 Carson Gee

from formunculous.models import *
from formunculous.forms import *
from formunculous.utils import build_template_structure, get_sub_app_fields

from django.conf import settings
from django import template
from django.shortcuts import get_object_or_404, render_to_response, get_list_or_404, redirect
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required
from django.core.paginator import InvalidPage, EmptyPage
from formunculous.utils.digg_paginator import DiggPaginator
from django.db.models import Q


def index(request, slug):
    """
       This shows all the completed applications for an application
       definition given by the slug.  The application definition index
       is provided in the apply view module.
    """
    
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    breadcrumbs = [{'url': reverse('formunculous-index'),
                    'name': _('Applications')},]

    # Check if they are authorized to view this page.
    validation = validate_user(request, ad)
    if validation:
        return validation

    # Create the base query
    apps = Application.objects.filter(app_definition = ad).exclude(submission_date=None)

    # Add search logic.  We will search all of the fields
    # defined.  Not just the header fields (in the future may
    # allow the user to specify the type of search.
    query = ''
    if "q" in request.GET:
        if request.GET['q']:
            query = request.GET['q']

            apps_query = None
            # Grab all the registered field types for generating the query
            fields = ad.fielddefinition_set.all()

            # Create a list of queries to chain together later
            queries = []
            for field in fields:
                queries.append(Q( Q(basefield__field_def__id = field.id) &\
                                      Q( **{'basefield__' +\
                                                field.type.lower().__str__() +\
                                                '__value__contains': query})))
            apps_query = queries.pop()
            for q in queries:
                apps_query |= q

            # Combine the base query and the search query
            apps = apps & Application.objects.filter(apps_query)

    # Because of the extended object nature of the app, sorting is a bit
    # complicated.  We need the FieldDefinition ID, and the field's class
    # in order to sort.

    # By default sort on date, since that is the only column I know
    # will be displayed
    reverse_sort = False
    field_def_sort = False
    sort_field_def_id = 0
    
    sort = "submission_date"
    sort_column = "0"

    if "s" in request.GET:
        sort_column = request.GET['s']
        if sort_column[0] == '-':
            reverse_sort = True
        sort_field_def_id = int(sort_column.lstrip('-'))

        # Special case of sorting by submission_date
        if sort_field_def_id == 0:
            sort = "submission_date"
        else:
            # Get the FieldDefinition type for use in the application
            # query.
            field_def = FieldDefinition.objects.get(id=sort_field_def_id)
            field_def_type = field_def.type.lower()
            sort = "basefield__%s__value" % field_def_type
            field_def_sort = True
    
    # Now do the actual sort LAST because we have to do the hinkyness
    # with the sorted field definition ID.

    if field_def_sort:
        # The reason for adding this basically pointless addition to the
        # query is that if there are multiple fields for one type
        # the DB will sort on the values of the first one, but if we
        # query for the specific instance of the field we want to sort on
        # the DB will sort on that instance of the type.
        apps = apps.filter(basefield__field_def__id = sort_field_def_id)

    apps = apps.order_by(sort)

    if reverse_sort:
        apps = apps.reverse()

    header_fields = ad.fielddefinition_set.filter(header=True)
    sort = ''

    headers = []
    for header in header_fields:
        sorted = False
        rev_sorted = False
        if sort_field_def_id == header.id and not reverse_sort:
            sort = '-%s' % header.id
            sorted = True
        elif sort_field_def_id == header.id and reverse_sort:
            sort = header.id
            rev_sorted = True
        else:
            sort = header.id
        header_dict = {'name': mark_safe(header.label),
                       'url': '%s?s=%s' % (reverse('reviewer-index',
                                                   kwargs={'slug':slug}),
                                           sort),
                       'sorted': sorted, 'rev_sorted': rev_sorted },
        headers += header_dict

    # Add on submission date
    rev_sorted = False
    sorted = False
    if sort_field_def_id == 0 and not reverse_sort:
        sort = '-0'
        sorted = True
    elif sort_field_def_id == 0 and reverse_sort:
        rev_sorted = True
        sort = 0
    else:
        sort = 0
    headers.append({'name': _('Submission Date and Time'),
                    'url': '%s?s=%s' % (reverse('reviewer-index',
                                                kwargs={'slug':slug}),
                                        sort),
                    'sorted': sorted, 'rev_sorted': rev_sorted, }
                   )

    # Paginate the apps before creating the table
    # so we only have to create the table for the page

    # Grab a default page size from settings if it exists, otherwise
    # use the default of 25
    try:
        if settings.FORMUNCULOUS_REVIEW_PAGE_SIZE:
            page_size = settings.FORMUNCULOUS_REVIEW_PAGE_SIZE
    except:
        page_size = 25

    paginator = DiggPaginator(apps, page_size, body=5, tail=2,
                              padding=2)

    # Get the current page, default to 1
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # Pull the correct page
    try:
        page_data = paginator.page(page)
    except (EmptyPage, InvalidPage):
        page_data = paginator.page(paginator.num_pages)

    # Now construct the value table of page of apps we have
    value_table = []
    for app in page_data.object_list:
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

    return render_to_response('formunculous/review_index.html',
                              { 'ad': ad, 'apps': apps,
                                'headers': headers,
                                'data': value_table,
                                'page': page_data,
                                'sort': sort_column,
                                'query': query,
                                'breadcrumbs': breadcrumbs},
                              context_instance=template.RequestContext(request))


def application(request, slug, app):

    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    app = get_object_or_404(Application, id=app)

    validation = validate_user(request, ad)
    if validation:
        return validation


    breadcrumbs = [{'url': reverse('formunculous-index'), 
                    'name': _('Application Index')},
                   {'url': reverse('reviewer-index', kwargs={'slug': slug}), 
                    'name':  ad.name},
                  ]

    message = ''
    if request.method == 'POST':
        if request.POST.has_key('save'):
            rev_form = ApplicationForm(ad, app, True, 
                                       request.POST, request.FILES)
            if rev_form.is_valid():
                rev_form.save()
                request.session['message'] = _('Form Data Saved')
                return redirect("reviewer-application", 
                                slug=slug, app=app.id)



    rev_form = ApplicationForm(ad, app, True)

    fields = build_template_structure(rev_form, ad, True)
    
    if 'message' in request.session:
        message = request.session['message']
        del request.session['message']

    sub_apps = get_sub_app_fields(app)


    return render_to_response('formunculous/review_application.html',
                              {'ad': ad, 'app': app,
                               'app_fields': app.get_field_values(),
                               'sub_apps': sub_apps,
                               'review_form': rev_form, 'fields': fields, 
                               'breadcrumbs': breadcrumbs, 
                               'message': message, },
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
            raise Http404, _('Application does not exist')

    return HttpResponse(_('Application Successfully Delete'))
delete = permission_required('formunculous.can_delete_applications')(delete)    

def validate_user(request, ad):
    # Check if they are authorized to view this page.
    if not (request.user.is_authenticated() \
                and request.user in ad.reviewers.all()):
        return render_to_response('formunculous/denied.html',
                                  context_instance=template.RequestContext(request))
    else:
        return None
        
