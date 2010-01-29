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


from django.conf.urls.defaults import *

urlpatterns = patterns('',

    # General views
    url(r'^$', 'formunculous.views.apply.index', name="formunculous-index"),

    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        name='formunculous-login',),

    url(r'^logout/$', 'formunculous.views.apply.logout_view',
        name='formunculous-logout',),

    # Apply views
    url(r'^forms/(?P<slug>[-\w]+)/?$', 'formunculous.views.apply.apply', name="formunculous-apply"),
    url(r'^confirm/(?P<slug>[-\w]+)/(?P<app>\d+)/$', 'formunculous.views.apply.confirm', name="formunculous-confirm"),
    url(r'^thankyou/(?P<slug>[-\w]+)/(?P<app>\d+)/$', 'formunculous.views.apply.thankyou', name="formunculous-thankyou"),
    url(r'^submit/(?P<slug>[-\w]+)/(?P<app>\d+)/$', 'formunculous.views.apply.submit', name="formunculous-submit"),

    # Reviewers views
    (r'^review/comments/', include('django.contrib.comments.urls')),
    url(r'^review/(?P<slug>[-\w]+)/$', 'formunculous.views.reviewer.index', name="reviewer-index"),
    url(r'^review/(?P<slug>[-\w]+)/(?P<app>\d+)/$', 'formunculous.views.reviewer.application', name="reviewer-application"),
    url(r'^review/(?P<slug>[-\w]+)/delete/$', 'formunculous.views.reviewer.delete', name="reviewer-delete"),

    # Builder views
    url(r'^builder/add/$', 'formunculous.views.builder.add_app_def', name="builder-add-ad"),
    url(r'^builder/edit/(?P<slug>[-\w]+)/$', 'formunculous.views.builder.modify_app_def', name="builder-edit-ad"),
    url(r'^builder/fields/(?P<slug>[-\w]+)/$', 'formunculous.views.builder.modify_fields', name="builder-edit-fields"),
    url(r'^builder/add/field/(?P<slug>[-\w]+)/$', 'formunculous.views.builder.add_field_form', name="builder-add-field"),
    url(r'^builder/add/dropdown/$', 'formunculous.views.builder.add_modify_dropdown', name="builder-add-dropdown"),
    url(r'^builder/delete/$', 'formunculous.views.builder.delete_app_def', name="builder-delete-ad"),
    url(r'^builder/copy/$', 'formunculous.views.builder.copy_app_def', name="builder-copy-ad"),
    url(r'^builder/preview/$', 'formunculous.views.builder.preview_app_def', name="builder-preview-ad"),

    url(r'^builder/subform/add/$', 'formunculous.views.builder.add_subapp_def', name="builder-add-subapp"),
    url(r'^builder/subform/change/$', 'formunculous.views.builder.change_subapp_def', name="builder-change-subapp"),

    url(r'^builder/?$', 'formunculous.views.builder.index', name="builder-index"),



    # File static server view
    url(r'^storage/(?P<ad_slug>[-\w]+)/(?P<app>\d+)/(?P<field_slug>[-\w]+)/(?P<file>.+)$',
        'formunculous.views.apply.file_view', name = "storage_view")
)
