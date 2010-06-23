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

# Create your views here.
from formunculous.models import *
from formunculous.forms import *
from formunculous.utils import build_template_structure, get_formsets, validate_formsets, save_formsets, fully_validate_formsets, get_sub_app_fields
from django import http
from django.utils.http import http_date
from django.db import models
from django.conf import settings
from django import template
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper

from django.contrib.auth import logout

from django.forms.formsets import formset_factory

import datetime
import mimetypes
import os
import stat


def index(request):

    """
    Displays a listing of all the available forms.  If the authenticated
    user is a flagged as a reviewer for any of the existing forms, links
    are provided for the review page of those forms.
    """

    app_defs = ApplicationDefinition.objects.current()

    app_coll = []
    for app_def in app_defs:
        status = _('N/A')
        if request.user.is_authenticated() and app_def.authentication:
            try:
                app = Application.objects.filter(user=request.user,
                       app_definition = app_def).order_by("id").reverse()[0]
                if app.submission_date:
                    status = _('Completed')
                else:
                    status = _('Started - Not Complete')
            except (Application.DoesNotExist, IndexError):
                status = _('Not Started')
        app_coll.append( {'app_def': app_def, 'status': status })

    review_apps = None
    if request.user.is_authenticated():
        
        review_apps = ApplicationDefinition.objects.reviewer(request.user)
    
    return render_to_response('formunculous/index.html',
                              {'app_coll': app_coll, 'review_apps': review_apps},
                              context_instance=template.RequestContext(request))

def apply(request, slug):

    """
    This is the primary form view.  It handles displaying the form
    defined by the slug, and redirecting to either of the completion
    states.  There are two primary branches, authenticated or
    unauthenticated.  If the app is authenticated it searches for
    an existing partial or full application from the user for the
    slug definition.  If it finds one, it displays either the partially
    completed form in an editable state, or a completion page if it is
    complete.
    """
    
    form = None
    app = None
    formsets = None
    history = None

    breadcrumbs = [{'url': reverse('formunculous-index'), 'name': _('Forms')},]

    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    if ad.parent:
        raise http.Http404, _("This application doesn't exist")

    if datetime.datetime.now() < ad.start_date or datetime.datetime.now() > ad.stop_date:
        raise http.Http404, _('This application is not active')

    # Require auth and redirect
    if ad.authentication:
        if not request.user.is_authenticated():
            return HttpResponseRedirect('%s?next=%s' % (reverse('formunculous-login'), request.path))


        # Grab the most recent app if it already exists.
        try:
            app = Application.objects.filter(
                user__username__exact=request.user.username,
                app_definition=ad).order_by('id').reverse()[0]
        except (Application.DoesNotExist, IndexError):
            pass

        # Got the app, if it is already submitted, render a different
        # template that displays the application's data unless the
        # application definition allows multiple submissions and the
        # user has requested a new instance.
        if app:

            new = False
            if request.GET.has_key('new'):
                new = True

            if app.submission_date and \
                    not (new and ad.authentication_multi_submit):
                # Load a custom template if it exists.
                try:
                    t = template.loader.get_template(
                        'formunculous/%s/completed.html' % ad.slug)

                    t = 'formunculous/%s/completed.html' % ad.slug
                except:
                    t = 'formunculous/completed.html'

                sub_apps = get_sub_app_fields(app)

                # If there are previous apps and this is a multi-auth
                # form, populate <history> with them
                if ad.authentication_multi_submit:
                    try:
                        apps_history = Application.objects.filter(
                            user__username__exact=request.user.username,
                            app_definition=ad).order_by('id').reverse()[1:]
                        if apps_history.count() > 0:
                            history = apps_history
                    except:
                        history = None

                
                return render_to_response(t,
                                          {'ad': ad, 'app': app, 
                                           'fields': app.get_field_values(),
                                           'sub_apps': sub_apps,
                                           'breadcrumbs': breadcrumbs, 
                                           'history': history, },
                                          context_instance=template.RequestContext(request))
            # If this is a new request and the existing app is finished,
            # create an additional app instance.
            if new and ad.authentication_multi_submit\
                   and app.submission_date:
                app = Application(user = request.user, app_definition = ad)
                app.save()


    # Begin form post processing.
    message = ''
    if request.method == 'POST':

        if request.POST.has_key('save'):
            # If this is the first save, create the app
            if not app:
                app = Application(app_definition = ad, user = request.user)
                app.save()
                
            form = ApplicationForm(ad, app, False, request.POST, request.FILES)
            if ad.applicationdefinition_set.all():
                formsets = get_formsets(ad, request, request.user)

            valid = True
            if not form.is_valid():
                valid = False
            if not validate_formsets(formsets):
                valid = False
            
            if valid:
                form.save()

                # Save formsets
                if formsets:
                    save_formsets(formsets, form.app, request.user)
                
                request.session['message'] = _('Form Data Saved')
                # Redirect to prevent repost
                return redirect("formunculous-apply", slug=slug)

        # If final submission, save form and redirect to the confirmation
        # page.
        elif request.POST.has_key('submit'):
            # If the app doesn't exist yet, create it
            if not app:
                user = None
                if ad.authentication:
                    user = request.user
                # Create the instance of the app
                app = Application(app_definition = ad, user = user)
            else:
                user = app.user

            form = ApplicationForm(ad, app, False, request.POST, request.FILES)
            
            # Walk through and grab the subapp formsets
            if ad.applicationdefinition_set.all():
                formsets = get_formsets(ad, request, user)
            # Check for required fields, and show errors before
            # redirect
            
            # Check for base form validity
            valid = True
            if not (form.is_valid() and form.check_required()):
                valid = False
            if not fully_validate_formsets(formsets):
                valid = False
            if valid:
                form.save()
                # Save subapps if there are any
                if formsets:
                    save_formsets(formsets, form.app, user)

                # Redirect to confirmation or thank you page
                if ad.authentication:
                    return redirect("formunculous-confirm", slug=slug, 
                                    app=app.id)
                else:
                    # Notify here, so refreshing doesn't resend notification
                    notify_reviewers(request, ad, app)
                    return redirect("formunculous-thankyou",slug=slug,
                                    app=app.id)

    # Grab form from formunculous.forms
    if not form:
        form = ApplicationForm(ad, app)

    fields = build_template_structure(form, ad)

    # Build user for use in subapps
    user = None
    if request.user and ad.authentication:
        user = request.user

    # Build sub forms based on sub application definitions
    if not formsets:
        formsets = []
        if ad.applicationdefinition_set.all():
            sub_apps = ad.applicationdefinition_set.all()
            for sub_app in sub_apps:
                sub_ad = sub_app.subapplicationdefinition_set.get()

                sub_app_formset = formunculous_subformset_factory(ApplicationForm,
                                              formset=FormunculousBaseFormSet,
                                              extra=sub_ad.extras,
                                              max_num = sub_ad.max_entries,)
                formset = sub_app_formset(app_def=sub_app, parent=app,user=user,
                                          minimum=sub_ad.min_entries, 
                                          prefix=sub_app.slug)
                formsets.append(formset)

    subforms = []
    for formset in formsets:
        forms = []
        for sub_form in formset.forms:
            forms.append({"form": sub_form,
                          "fields": build_template_structure(sub_form,
                                                             formset.app_def)})
        subforms.append({ "sub_ad": formset.app_def, "forms": forms,
                          "formset": formset})
                
            
            

    # Try a customized template.
    # if it is there use it, else use the default template.
    try:
        t = template.loader.get_template('formunculous/%s/apply.html' % ad.slug)
        t = 'formunculous/%s/apply.html' % ad.slug
    except:
        t = 'formunculous/apply.html'

    if 'message' in request.session:
        message = request.session['message']
        del request.session['message']

    # If there are previous apps and this is a multi-auth
    # form, populate <history> with them
    if ad.authentication_multi_submit:
        try:
            apps_history = Application.objects.filter(
                user__username__exact=request.user.username,
                app_definition=ad, ).exclude(submission_date=None).order_by('id').reverse()
            if apps_history.count() > 0:
                history = apps_history
        except:
            history = None


    return render_to_response(t,
                              {'form': form, 'ad': ad, 'fields': fields,
                               'subforms': subforms, 
                               'message': message,
                               'breadcrumbs': breadcrumbs, 
                               'history': history, },
                              context_instance=template.RequestContext(request))


    

def confirm(request, slug, app):
    """
       This confirms that the user wishes to finish their
       authenticated form. If it is confirmed they are sent to
       submit.  If it is cancelled they returned to the apply page.

       When rendering, try to load a custom template based on
       the slug.  If it isn't there, load the default template.
    """
    
    app = get_object_or_404(Application, id=app)
    ad = get_object_or_404(ApplicationDefinition, slug=slug)
    sub_apps = get_sub_app_fields(app)

    try:
        t = template.loader.get_template('formunculous/%s/confirm.html'
                                         % ad.slug)
        t = 'formunculous/%s/confirm.html' % ad.slug
    except:
        t = 'formunculous/confirm.html'


    return render_to_response(t,
                              {'fields': app.get_field_values(), 'ad': ad,
                               'app': app, 'sub_apps': sub_apps},
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
       reviewers.

       When rendering, try to load a custom template based on
       the slug.  If it isn't there, load the default template.
    """
    app = get_object_or_404(Application, id=app)
    ad = get_object_or_404(ApplicationDefinition, slug=slug)

    
    
    app.submission_date = datetime.datetime.now()
    app.save()

    # Build the template context before deleting the form.
    try:
        t = template.loader.get_template('formunculous/%s/thankyou.html'
                                         % ad.slug)
        t = 'formunculous/%s/thankyou.html' % ad.slug
    except:
        t = 'formunculous/thankyou.html'

    sub_apps = get_sub_app_fields(app)

    t = template.loader.get_template(t)
    c = template.RequestContext( request, {'ad': ad,
                                           'fields': app.get_field_values(),
                                           'sub_apps': sub_apps })

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

    sub_apps = []

    if ad.email_only:
        t = 'formunculous/email_application.html'
        sub_apps = get_sub_app_fields(app)
    else:
        t = 'formunculous/notify_reviewers_email.html'

    body = render_to_string(
        t,
        { 'ad': ad, 'app': app, 'fields': app.get_field_values(), 
          'sub_apps': sub_apps, 'site': Site.objects.get_current(), },
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
        if sub_apps:
            for sub_app_group in sub_apps:
                for sub_app in sub_app_group['sub_apps']:
                    for field in sub_app['fields']:
                        try:
                            if issubclass(field['data'].field.__class__, models.FileField):
                                email.attach_file(field['data'].path)
                        except:
                            pass
                            
                

    email.send(fail_silently=True)


def history(request):

    if not request.method == "POST":
        raise http.Http404, _('Invalid Method')
    if not request.POST.has_key('app'):
        raise http.Http404, _('Invalid Method')


    app = get_object_or_404(Application, id=request.POST['app'])

    if not app.user.username == request.user.username:
        return HttpResponse("You are not authorized to view this form.")

    # Build the template context before deleting the form.
    try:
        t = template.loader.get_template('formunculous/%s/apply_history.html'
                                         % app.app_definition.slug)
        t = 'formunculous/%s/apply_history.html' % app.app_definition.slug
    except:
        t = 'formunculous/apply_history.html'

    sub_apps = get_sub_app_fields(app)
    t = template.loader.get_template(t)
    c = template.RequestContext( request, {'ad': app.app_definition,
                                           'fields': app.get_field_values(),
                                           'sub_apps': sub_apps })
    return HttpResponse(t.render(c))

def logout_view(request):

    """
       Redirect to the location in the "next" key on logout, or
       redirect to the index page if there is no next key specified.
    """

    logout(request)
    if request.GET.has_key('next'):
        return HttpResponseRedirect(request.GET['next'])
    else:
        return redirect("formunculous-index")



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
            not(request.user == app.user or request.user in ad.reviewers.all()):
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
        raise http.Http404, _('The specified file is not the correct type')

    if not os.path.isfile(file_field.path) or not os.access(file_field.path, os.R_OK):
        raise http.Http404, _('"%s" does not exist' % file)

    statobj = os.stat(file_field.path)
    mimetype = mimetypes.guess_type(file_field.path)[0] or 'application/octet-stream'
    contents = open(file_field.path, 'rb')
    wrapper = FileWrapper(contents)
    response = http.HttpResponse(wrapper, mimetype=mimetype)
    response["Last-Modified"] = http_date(statobj[stat.ST_MTIME])
    response["Content-Length"] = os.path.getsize(file_field.path)

    return response
