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
from django.contrib.sites.models import Site

from formunculous.utils.digg_paginator import DiggPaginator
from django.db.models import Q

# Zip file serving imports
import zipfile
import os
import tempfile
from django.core.servers.basehttp import FileWrapper

#Flash Charting
from formunculous.utils.ofc2.OpenFlashChart import *
import time


def index(request, slug):
    """
    This shows all the completed applications for an application
    definition given by the slug.  The application definition index
    is provided in the apply view module.
    """
    
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    breadcrumbs = [{'url': reverse('formunculous-index'),
                    'name': _('Forms')},]

    # Check if they are authorized to view this page.
    validation = validate_user(request, ad)
    if validation:
        return validation

    # Create the base query
    apps = Application.objects.filter(Q(app_definition = ad) 
                                      & ~Q(submission_date=None))

    # Add search logic.  We will search all of the fields
    # defined.  Not just the header fields (in the future may
    # allow the user to specify the type of search.
    query = ''
    if "q" in request.GET:
        if request.GET['q']:
            query = request.GET['q']
            query = query.strip()

            apps_query = None
            # Grab all the registered field types for generating the query
            fields = ad.fielddefinition_set.all()

            # Create a list of queries to chain together later
            queries = []
            for field in fields:
                queries.append(Q( Q(basefield__field_def__id = field.id) &\
                                      Q( **{'basefield__' +\
                                                field.type.lower().__str__() +\
                                                '__value__icontains': query})))
            apps_query = queries.pop()
            for q in queries:
                apps_query |= q

            # Combine the base query and the search query
            apps = apps & Application.objects.filter(apps_query)

    # Because of the extended object nature of the app, sorting using
    # SQL isn't possible using anything other than the date.  So if we
    # are sorting by something else, grab the full result set of values
    # put them into a python list of dicts and grab the sort field
    # for each app id, then pass the sorted list into the pager.
    # A little inefficient, but there isn't much of a choice.

    # By default sort on the submission date in reverse, since that is
    # the only column I know will be displayed
    reverse_sort = True
    field_def_sort = False
    sort_field_def_id = 0
    
    sort = "submission_date"
    sort_column = "-0"

    if "s" in request.GET:
        sort_column = request.GET['s']
        if not sort_column[0] == '-':
            reverse_sort = False
        sort_field_def_id = int(sort_column.lstrip('-'))

        # Special case of sorting by submission_date
        if sort_field_def_id == 0:
            sort = "submission_date"
        else:
            # Get the FieldDefinition type for use in the application
            # query.
            sort = None
            field_def = FieldDefinition.objects.get(id=sort_field_def_id)
    
    if sort:
        apps = apps.order_by(sort)

    if reverse_sort and sort:
        apps = apps.reverse()

    apps = apps.distinct().values_list('id', flat=True)


    app_id_list = [{'app_id': a} for a in apps] 

    # Check if we are not sorted by date, and go through and create
    # the sort order
    if not sort:
        app_id_list =  [{'app_id': a} for a in apps] 
        # Add the sorting column to the list
        for app_id in app_id_list:
            app_id['sorter'] = Application.objects.\
                get(id=app_id['app_id']).\
                get_field_value(field_def.slug)
        # Sort the newly created list
        app_id_list.sort(lambda x, y: cmp(x['sorter'], y['sorter']), 
                         reverse=reverse_sort)



    # Build the headers with proper urls for updating the sort order
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
        page_size = 50

    paginator = DiggPaginator([a['app_id'] for a in app_id_list], page_size, body=5, tail=2,
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


    for app_id in page_data.object_list:

        app = Application.objects.get(id=app_id)
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

    # Are there partially completed applications?
    partials = False

    if Application.objects.filter(app_definition=ad, submission_date=None).count():
        partials = True

    status = None
    if request.session.has_key('status'):
        if int(request.session['status']) == 1:
            status = _('There are currently no files associated with \
                              this application')
        del request.session['status']


    return render_to_response('formunculous/review_index.html',
                              { 'ad': ad, 
                                'headers': headers,
                                'data': value_table,
                                'page': page_data,
                                'sort': sort_column,
                                'query': query,
                                'partials': partials,
                                'status': status,
                                'breadcrumbs': breadcrumbs},
                              context_instance=template.RequestContext(request))


def index_incomplete(request, slug):
    """
    This shows all the completed applications for an application
    definition given by the slug.  The application definition index
    is provided in the apply view module.
    """
    
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    breadcrumbs = [{'url': reverse('formunculous-index'),
                    'name': _('Forms')},]

    # Check if they are authorized to view this page.
    validation = validate_user(request, ad)
    if validation:
        return validation

    # Create the base query
    apps = Application.objects.filter(app_definition = ad, submission_date=None)

    headers = [_('Form ID'), _('User'), _('Percent Complete'),]
    
    data_table = []
    for app in apps:
        
        username = _('None')
        if app.user:
            username = app.user.username

        data_row = [ app.id, username, ]
        fields = app.get_field_values()
        total = len(fields) + 1
        num_complete = 0
        for field in fields:
            if field['data']:
                num_complete+=1
        percent = float(num_complete)/float(total) * 100.0
        data_row.append( "%1.2f%%" % percent )
        data_row.append(app.id)
        data_table.append(data_row)
        
        


    return render_to_response('formunculous/review_index_incomplete.html',
                              { 'ad': ad,
                                'headers': headers,
                                'data': data_table,
                                'breadcrumbs': breadcrumbs},
                              context_instance=template.RequestContext(request))


def statistics(request, slug):

    """
    This view display response statistics for a given application definition
    using open-flash-chart-2 for displaying graphs of responses over time and
    percentage statistics for dropdown questions.
    """

    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    validation = validate_user(request, ad)
    if validation:
        return validation


    breadcrumbs = [{'url': reverse('formunculous-index'), 
                    'name': _('Form Index')},
                   {'url': reverse('reviewer-index', kwargs={'slug': slug}), 
                    'name':  ad.name},
                   ]

    fields = []
    for field in ad.fielddefinition_set.all():
        if field.dropdownchoices_set.all():
            fields.append(field)

    for sub_ad in ad.applicationdefinition_set.all():
        for field in sub_ad.fielddefinition_set.all():
            if field.dropdownchoices_set.all():
                fields.append(field)

    return render_to_response('formunculous/review_statistics.html',
                              {'ad': ad,
                               'breadcrumbs': breadcrumbs, 
                               'fields': fields,
                               },
                              context_instance=template.RequestContext(request))

def response_over_time(request, slug):

    
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    validation = validate_user(request, ad)
    if validation:
        return validation
    
    apps = Application.objects.filter(app_definition = ad).\
        exclude(submission_date=None)
    

    values = []
    min_date = apps[0].submission_date
    max_date = apps[apps.count()-1].submission_date
    max_count = 0
    for day in range( (max_date - min_date).days + 1):
        curr_date = min_date + datetime.timedelta(day)
        app_count = apps.filter(
            submission_date__gte = curr_date.date(),
            submission_date__lt = (curr_date + datetime.timedelta(days=1))\
                .date()).count()

        if app_count > max_count:
            max_count = app_count

        values.append({'x':int(time.mktime(curr_date.timetuple())),'y': app_count}),

    element = Chart()
    element.values = values
    element.type = "scatter_line"
    element.colour = "#aaaaff"
    element.width = 5
    element.dot_style.type = "hollow-dot"
    element.dot_style.dot_size = 5
    element.dot_style.halo_size = 0
    element.dot_style.tip = "#date:d M y#<br>Form Completions: #val#"
    
    chart = Chart()
    chart.y_axis.min = 0
    chart.y_axis.max = max_count + 1
    chart.y_axis.steps = 1
    chart.y_axis.colour = "#999999"
    chart.y_axis.grid_colour = '#f1f1f1'
    chart.y_axis.labels = { 'colour': '#333333' }
    chart.y_axis.label = _("Number of Responses")
    chart.y_legend.text =  _("Completed Forms")
    chart.y_legend.style =  "{font-size: 14px; font-weight: bold; color: #666666}"
    
    chart.x_axis.min = int(time.mktime(min_date.timetuple()))
    chart.x_axis.max = int(time.mktime(max_date.timetuple()))
    chart.x_axis.grid_colour = '#f1f1f1'
    chart.x_axis.colour = "#999999"
    chart.x_axis.steps = 86400
    chart.x_axis.labels = { 'text': '#date:l jS, M Y#', 'steps': 86400,
                            'visible-steps': 7, 'rotate': 300, 'colour': '#333333' }
    chart.x_legend.text =  _("Days")
    chart.x_legend.style =  "{font-size: 14px; font-weight: bold; color: #666666}"
    
    chart.title.text = "%s Form Responses Over Time" % ad.name
    chart.title.style = "{font-size: 20px; color: #aaaaff; font-weight: bold;}"
    chart.bg_colour = "#ffffff"
    
    chart.elements = [element]
    
    return HttpResponse(chart.create())


import random
def field_pie(request, slug, field):

    """
    Returns the JSON data for dropdown choice selection stats of the 
    field that is passed in.
    """
    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    field = get_object_or_404(FieldDefinition, id=int(field))

    validation = validate_user(request, ad)
    if validation:
        return validation

    options = field.dropdownchoices_set.all()
    values = {}
    for option in options:
        values[ option.value ] = 0

    field_model = eval(field.type)
    responses = [a.value for a in field_model.objects.filter(field_def = field)]
    total_count = 0
    for response in responses:
        if values.has_key(response):
            values[response]+=1
            total_count += 1

    # I have the data generate the chart
    element = Chart()
    element.values = [{'value': values[key], 'label': key, 'label-colour': '#666666',} for key in values.keys()]
    element.type = "pie"
    element.alpa = ".6"
    element.start_angle = 35
    element.animate = {"type": "fade" }
    element.gradient_fill = True
    element.tip = '#val# of #total#<br>#percent# of 100%'
    element.colours = [ "#%s%s%s" % (hex(random.randint(0,255))[2:],
                                               hex(random.randint(0,255))[2:],
                                               hex(random.randint(0,255))[2:]) for x in range(options.count())]

    chart = Chart()
    chart.title.text = "%s Selections" % field.label
    chart.title.style = "{font-size: 20px; color: #aaaaff; font-weight: bold;}"
    chart.bg_colour = "#ffffff"
    
    chart.elements = [element]
    
    return HttpResponse(chart.create())

def application(request, slug, app):

    """
    The reviewer view of a specific application.  Displays and handles
    a form for the reviewer only fields, and displays comments.
    """

    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    app = get_object_or_404(Application, id=app)

    validation = validate_user(request, ad)
    if validation:
        return validation


    breadcrumbs = [{'url': reverse('formunculous-index'), 
                    'name': _('Form Index')},
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
            raise Http404, _('Form does not exist')

    return HttpResponse(_('Form Successfully Deleted'))
delete = permission_required('formunculous.can_delete_applications')(delete)


def export_csv(request, slug):

    """
    Gets all application data (including sub applications), and returns
    a CSV file over HTTP.  This does not currently do any data filtering.
    """
    
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    # Check if they are authorized to view this page.
    validation = validate_user(request, ad)
    if validation:
        return validation

    headers = []
    # Get base set of headers, if we have sub apps grab those, and keep track of
    # how many headers there are of those.  This will do a many rows for each
    # parent style of csv for one-to-many forms.

    field_definitions = ad.fielddefinition_set.all()
    base_form_field_count = field_definitions.count()
    for field in field_definitions:
        headers.append(field.label)
    
    # Add user name and submission_date
    headers.append(_('Username'))
    headers.append(_('Submission Date'))
    base_form_field_count += 2

    sub_form_field_counts = []
    sub_ads = ad.applicationdefinition_set.all().order_by("slug")
    for sub_ad in sub_ads:
        sub_ad_fields = sub_ad.fielddefinition_set.all()
        sub_form_field_counts.append(sub_ad_fields.count())
        for field in sub_ad_fields:
            headers.append(sub_ad.name + "_" + field.label)


    # Column headings are built, now populate with data

    # Create the base query
    apps = Application.objects.filter(app_definition = ad).exclude(submission_date=None).order_by("submission_date")

    data_table = []
    for app in apps:
        data_row = [a['data'] for a in app.get_field_values(all_fields=True)]
        if app.user:
            data_row.append(app.user.username)
        else:
            data_row.append('')

        data_row.append(app.submission_date.strftime("%a %e %b %Y %r"))

        data_table.append(data_row)

        # Now do the sub relations
        sub_ad_count = 0
        for sub_ad in sub_ads:
            for sub_app in app.application_set.filter(app_definition = sub_ad):
                data_row = []
                # Add padding to beginning
                data_row.extend(["" for a in range(
                            sum(int(v) for v in sub_form_field_counts[:sub_ad_count])
                            + base_form_field_count
                            )])
                # Add the actual data
                data_row.extend([ a['data'] for a in sub_app.get_field_values()])
                # Add padding to the end
                data_row.extend(["" for a in range(
                            sum(
                                int(v) for v in sub_form_field_counts[sub_ad_count+1:])
                            )])
                data_table.append(data_row)
            sub_ad_count+=1

    # Build the CSV output format
    output = ""
    for header in headers:
        output+= '"' + header + '",'
    output+="\n"
    for row in data_table:
        for item in row:
            if item:

                # See if it is a data type that doesn't have a 
                # string representation of data, but links to it
                # (i.e. Files, Images, etc) 
                try:
                    output+= '"http://' + Site.objects.get_current().domain \
                        + item.url + '",'
                except:
                    output+= '"' + str(item) + '",'
            else:
                output+= '"",'
        output+= "\n"

    # Build the Http headers
    response = HttpResponse(mimetype='text/csv')
    filename = ad.name + datetime.date.today().strftime("%d%b%Y") + '.csv'
    response['Content-Disposition'] = 'attachment; filename=%s' % filename.replace(' ', '_')
    response.write(output)

    return response


def export_zip(request, slug):
    """
    This will create a zip file of all the files associated with an application
    definition.  It will create them in the form appid_fieldslug_filename
    """

    # Get app def and validate user
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    # Check if they are authorized to view this page.
    validation = validate_user(request, ad)
    if validation:
        return validation

    # Create zip file for storing the attached files
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix='blah')
        zip_file = zipfile.ZipFile(temp_file, mode='w')
    except:
        raise HttpResponse.Http404, _('Unable to create temporary file')

    # Get all the file subclassed fields from all apps and sub_forms
    apps = Application.objects.filter(app_definition = ad).exclude(submission_date=None)
    for app in apps:

        fields = app.get_field_values(all_fields=True)
        for field in fields:
            try:
                if issubclass(field['data'].field.__class__, models.FileField):
                    if os.path.isfile(field['data'].path) \
                            and os.access(field['data'].path, os.R_OK):
                        try:
                            zip_file.write(field['data'].path,
                                           arcname="%s_%s_%s" 
                                           % (app.id, 
                                              field['label'].encode('latin-1'),
                                              os.path.basename(field['data'].name).encode('latin-1')
                                              ))
                        except:
                            # Shouldn't happen, but not worth stopping zip file
                            # creation for.
                            pass
            except:
                # Not a field class
                pass
        sub_apps = app.application_set.all()
        for sub_app in sub_apps:
            fields = sub_app.get_field_values(all_fields=True)
            for field in fields:
                try:
                    if issubclass(field['data'].field.__class__, models.FileField):
                        if os.path.isfile(field['data'].path) \
                                and os.access(field['data'].path, os.R_OK):
                            try:
                                zip_file.write(field['data'].path,
                                               arcname="%s_%s_%s_%s"
                                               % (app.id, 
                                                  sub_app.app_definition.name.encode('latin-1'),
                                                  field['label'].encode('latin-1'),
                                                  os.path.basename(field['data'].name).encode('latin-1')
                                                  ))
                            except:
                                pass
                except:
                    pass

    zip_file.close()
    
    if not len(zip_file.namelist()) >  0:
        temp_file.close()
        # No files associated with this application definition, so redirect back
        # to the review index and set a request value so the index knows what
        # happened and can display a message to the user.
        request.session['status'] = 1
        return redirect('reviewer-index', slug=ad.slug)

    # There are files in the zip, build a response to serve the file
    wrapper = FileWrapper(temp_file)

    response = HttpResponse(wrapper, content_type='application/zip')
    filename = ad.name + datetime.date.today().strftime("%d%b%Y") + '.zip'
    response['Content-Disposition'] = 'attachment; filename=%s' % filename.replace(' ', '_')
    response['Content-Length'] = temp_file.tell()
    temp_file.seek(0)

    return response

def validate_user(request, ad):
    # Check if they are authorized to view this page.
    if not (request.user.is_authenticated() \
                and request.user in ad.reviewers.all()):
        return render_to_response('formunculous/denied.html',
                                  context_instance=template.RequestContext(request))
    else:
        return None
    
