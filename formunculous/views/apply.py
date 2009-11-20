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
from django import http
from django.utils.http import http_date
from django.db import models
from django.conf import settings
from django import template
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

import datetime
import mimetypes
import os
import stat


def index(request):

    app_defs = ApplicationDefinition.objects.current()

    app_coll = []
    for app_def in app_defs:
        status = _('N/A')
        if request.user.is_authenticated() and app_def.authentication:
            try:
                app = Application.objects.get(user=request.user,
                                              app_definition = app_def)
                if app.submission_date:
                    status = _('Completed')
                else:
                    status = _('Started - Not Complete')
            except Application.DoesNotExist:
                status = _('Not Started')
        app_coll.append( {'app_def': app_def, 'status': status })

    review_apps = None
    if request.user.is_authenticated():
        
        review_apps = ApplicationDefinition.objects.reviewer(request.user)
    
    return render_to_response('formunculous/index.html',
                              {'app_coll': app_coll, 'review_apps': review_apps},
                              context_instance=template.RequestContext(request))

def apply(request, slug):
    
    form = None
    app = None

    breadcrumbs = [{'url': reverse('formunculous-index'), 'name': _('Applications')},]

    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    if datetime.datetime.now() < ad.start_date or datetime.datetime.now() > ad.stop_date:
        raise http.Http404, _('This application is no longer active')

    # Require auth and redirect
    if ad.authentication:
        if not request.user.is_authenticated():
            return HttpResponseRedirect('%s?next=%s' % (reverse('formunculous-login'), request.path))

        # Grab the app if it already exists.
        try:
            app = Application.objects.get(user__username__exact=request.user.username, app_definition=ad)
        except Application.DoesNotExist:
            pass

        # Got the app, if it is already submitted, render a different
        # template that displays the application's data.
        if app:
            if app.submission_date:
                return render_to_response('formunculous/completed.html',
                                          {'ad': ad, 'app': app, 
                                           'fields': app.get_field_values(),
                                           'breadcrumbs': breadcrumbs, },
                                          context_instance=template.RequestContext(request))
    message = ''
    if request.method == 'POST':

        if request.POST.has_key('save'):
            # If this is the first save, create the app
            if not app:
                app = Application(app_definition = ad, user = request.user)
                app.save()
            form = ApplicationForm(ad, app, False, request.POST, request.FILES)
            if form.is_valid():
                form.save()
                message = _('%s Application Data Saved' % ad.name)
                # Redirect to prevent repost
                return redirect("formunculous-apply", slug=slug)

        # If final submission, save form and redirect to the confirmation
        # page.
        if request.POST.has_key('submit'):
            # If the app doesn't exist yet, create it
            if not app:
                user = None
                if ad.authentication:
                    user = request.user
                # Create the instance of the app
                app = Application(app_definition = ad, user = user)

            form = ApplicationForm(ad, app, False, request.POST, request.FILES)
            # Check for required fields, and show errors before
            # redirect
            if form.is_valid() and form.check_required():

                form.save()

                # Redirect to confirmation or thank you page
                if ad.authentication:
                    return redirect("formunculous-confirm", slug=slug, app=app.id)
                else:
                    return redirect("formunculous-thankyou",slug=slug, app=app.id)

    # Grab form from formunculous.forms
    if not form:
        form = ApplicationForm(ad, app)

    # create structure for the template that looks like
    # form-> (group, pre-text, post-text, page)
    inc = {}
    fields = []
    for field in ad.fielddefinition_set.filter(reviewer_only=False):
        field_dict = {'group': field.group, 'pre_text': mark_safe(field.pre_text), 
                      'post_text': mark_safe(field.post_text),
                      'field': form.__getitem__(field.slug),
                      'required': field.require},
        fields += field_dict
        inc[field.slug] = True

    # Got all the DB fields in the form, now run through any extras that
    # may have shown up.
    for field in form.fields:
        if not inc.has_key(field):
            field_dict = {'group': None, 'pre_text': None, 'post_text': None,
                         'field': form.__getitem__(field), 
                         'required': form.__getitem__(field).field.required,},
            fields += field_dict
    

    # Try a customized template.
    # if it is there use it, else use the default template.
    try:
        t = template.loader.get_template('formunculous/%s/apply.html' % ad.slug)
        t = 'formunculous/%s/apply.html' % ad.slug
    except:
        t = 'formunculous/apply.html'
    return render_to_response(t,
                              {'form': form, 'ad': ad, 'fields': fields, 'message': message,
                               'breadcrumbs': breadcrumbs, },
                              context_instance=template.RequestContext(request))
    

def confirm(request, slug, app):
    """
       This confirms that the user wishes to finish their authenticated formunculous.
       If it is confirmed they are sent to submit.  If it is cancelled they
       returned to the apply page.
    """
    
    app = get_object_or_404(Application, id=app)
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    return render_to_response('formunculous/confirm.html',
                              {'fields': app.get_field_values(), 'ad': ad,
                               'app': app, },
                              context_instance=template.RequestContext(request))

def submit(request, slug, app):
    """
       This adds a datestamp to the application and prevents it from being
       viewed again.  If the application is a non-authenticated app, then
       there is no storage, and the application is presented again.

       If the application is authenticated, then the user is redirected
       to a new view of their completed application, which displays a message
       to the user that no further changes can be made, and displays their
       responses.
    """
    app = get_object_or_404(Application, id=app)
    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    
    app.submission_date = datetime.datetime.now()
    app.save()

    notify_reviewers(request, ad, app)

    # If this is an email_only AD, then delete everything in the application
    # except for the application stub (so they can't multi-submit).
    if ad.email_only:
        field_set = ad.fielddefinition_set.all()
        for field_def in field_set:
            field_model = eval(field_def.type)
            try:
                field_val = field_model.objects.get( app = app, field_def = field_def)
                field_val.delete()
            except:
                pass # No value entered, nothing to delete.
    
    return redirect("formunculous-apply", slug=slug)

def thankyou(request, slug, app):
    """
       This is the completion page for non-authenticated applications.
       It flags the app with a submission date and notifies all of the
       reviewers
    """
    app = get_object_or_404(Application, id=app)
    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    
    app.submission_date = datetime.datetime.now()
    app.save()

    notify_reviewers(request, ad, app)

    # Build the template context before deleting the formunculous.
    t = template.loader.get_template('formunculous/thankyou.html')
    c = template.RequestContext( request, {'ad': ad, 'fields': app.get_field_values(),})

    # If this is an email_only AD, delete the application completely now that
    # we have fired off the email.
    if ad.email_only:
        app.delete()

    return HttpResponse(t.render(c))

def notify_reviewers(request, ad, app):
    """
       This sends a templated email to all of the listed reviewers if
       notifications are turned on and there are listed reviewers
    """
    
    if not (ad.notify_reviewers or ad.notify_owner):
        return None

    fields = app.get_field_values()

    if ad.email_only:
        t = 'formunculous/email_formunculous.html'
    else:
        t = 'formunculous/notify_reviewers_email.html'

    body = render_to_string(
        t,
        { 'ad': ad, 'app': app, 'fields': app.get_field_values(), 
          'site': Site.objects.get_current(), },
        context_instance=template.RequestContext(request))

    notify_list = []
    
    if ad.notify_reviewers:
        notify_list = [a.email for a in ad.reviewers.all()]

    if ad.notify_owner:
        notify_list.append(ad.owner)

    email = EmailMessage(_('[%s] Completed' % ad.name), body,
                settings.SERVER_EMAIL, notify_list)

    # Before we send see if this is a full email, or just a URL notification
    # and attach any files included
    if ad.email_only:
        for field in fields:
            try:
                if issubclass(field['data'].field.__class__, models.FileField):
                    email.attach_file(field['data'].path)
            except:
                pass

    email.send(fail_silently=True)


def file_view(request, ad_slug, app, field_slug, file):
    """
       Check permissions, based on fields, and serve content or a permission
       denied page.

       The reviewers of a specified app definition can view all files.
       The user who filled out an app can view the files.
       For anonymous apps all files can be viewed by anyone if they can guess
       the url.
    """
    ad = get_object_or_404(ApplicationDefinition, slug=ad_slug)
    app = get_object_or_404(Application, id=app)
    field_def = get_object_or_404(FieldDefinition, slug=field_slug)

    if ad.authentication and not request.user.is_authenticated():
        return HttpResponseRedirect('/accounts/login/?next=%s' % request.path)

    # If the application is not anonymous and the user isn't either a reviewer
    # or the applicant, deny access.
    if ad.authentication and \
            not(request.user is app.user or request.user in ad.reviewers.all()):
        return render_to_response('formunculous/denied.html',
                                  context_instance=template.RequestContext(request))

    # If the field definition is for reviewers only and the current user isn't
    # in the reviewer list, deny access.
    if ad.authentication and \
            field_def.reviewer_only and not request.user in ad.reviewers.all():
        return render_to_response('formunculous/denied.html',
                                  context_instance=template.RequestContext(request))
        

    # Passed permission requirements, serve the file
    # Get the full path
    file_field = app.get_field_value(field_slug)
    if not file_field:
        raise http.Http404, _('"%s" does not exist' % file)
    
    if not issubclass(file_field.field.__class__, models.FileField):
        raise http.Http500, _('The specified file is not the correct type')

    if not os.path.isfile(file_field.path) or not os.access(file_field.path, os.R_OK):
        raise http.Http404, _('"%s" does not exist' % file)

    statobj = os.stat(file_field.path)
    mimetype = mimetypes.guess_type(file_field.path)[0] or 'application/octet-stream'
    contents = open(file_field.path, 'rb').read()
    response = http.HttpResponse(contents, mimetype=mimetype)
    response["Last-Modified"] = http_date(statobj[stat.ST_MTIME])
    response["Content-Length"] = len(contents)
    return response
