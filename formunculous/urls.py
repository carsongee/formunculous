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

from django.conf.urls import patterns, include, url
from formunculous.views import builder

urlpatterns = patterns('',

    # General views
    url(r'^$', 'formunculous.views.apply.index', name="formunculous-index"),

    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        name='formunculous-login',),

    url(r'^logout/$', 'formunculous.views.apply.logout_view',
        name='formunculous-logout',),

    # Apply views
    url(r'^forms/(?P<slug>[-\w]+)/?$',
        'formunculous.views.apply.apply',
        name="formunculous-apply"
    ),
    url(r'^confirm/(?P<slug>[-\w]+)/(?P<app>\d+)/$',
        'formunculous.views.apply.confirm',
        name="formunculous-confirm"
    ),
    url(r'^thankyou/(?P<slug>[-\w]+)/(?P<app>\d+)/$',
        'formunculous.views.apply.thankyou',
        name="formunculous-thankyou"
    ),
    url(r'^submit/(?P<slug>[-\w]+)/(?P<app>\d+)/$', 
        'formunculous.views.apply.submit',
        name="formunculous-submit"),
    url(r'^history/$',
        'formunculous.views.apply.history',
        name="formunculous-apply-history"
    ),

    # Reviewers views
    (r'^review/comments/', include('django.contrib.comments.urls')),
    url(r'^review/(?P<slug>[-\w]+)/$',
        'formunculous.views.reviewer.index',
        name="reviewer-index"
    ),
    url(r'^review/(?P<slug>[-\w]+)/incomplete/?$',
        'formunculous.views.reviewer.index_incomplete',
        name="reviewer-index-incomplete"
    ),
    url(r'^review/(?P<slug>[-\w]+)/statistics/?$',
        'formunculous.views.reviewer.statistics',
        name="reviewer-statistics"
    ),
    url(r'^review/(?P<slug>[-\w]+)/response-vs-time/?$',
        'formunculous.views.reviewer.response_over_time',
        name="reviewer-stats-response-vs-time"
    ),
    url(r'^review/(?P<slug>[-\w]+)/field-pie/(?P<field>\d+)/?$',
        'formunculous.views.reviewer.field_pie',
        name="reviewer-stats-field-pie"
    ),
    url(r'^review/(?P<slug>[-\w]+)/delete/$',
        'formunculous.views.reviewer.delete',
        name="reviewer-delete"
    ),
    url(r'^review/(?P<slug>[-\w]+)/export/$',
        'formunculous.views.reviewer.export_csv',
        name="reviewer-export"
    ),
    url(r'^review/(?P<slug>[-\w]+)/export_zip/$',
        'formunculous.views.reviewer.export_zip',
        name="reviewer-export-zip"
    ),
    url(r'^review/(?P<slug>[-\w]+)/(?P<app>\d+)/$',
        'formunculous.views.reviewer.application',
        name="reviewer-application"),

    # Builder views
    url(r'^builder/add/$',
        builder.AddAppDef.as_view(),
        name="builder-add-ad"
    ),
    url(r'^builder/edit/(?P<slug>[-\w]+)/$',
        builder.ModifyAppDef.as_view(),
        name="builder-edit-ad"
    ),
    url(r'^builder/fields/(?P<slug>[-\w]+)/$',
        builder.ModifyFields.as_view(),
        name="builder-edit-fields"
    ),
    url(r'^builder/add/field/(?P<slug>[-\w]+)/$',
        builder.AddFieldForm.as_view(),
        name="builder-add-field"
    ),
    url(r'^builder/add/dropdown/$',
        builder.AddModifyDropDown.as_view(),
        name="builder-add-dropdown"
    ),
    url(r'^builder/delete/$',
        builder.DeleteAppDef.as_view(),
        name="builder-delete-ad"
    ),
    url(r'^builder/copy/$',
        builder.CopyAppDef.as_view(),
        name="builder-copy-ad"
    ),
    url(r'^builder/preview/$',
        builder.PreviewAppDef.as_view(),
        name="builder-preview-ad"
    ),
    url(r'^builder/subform/add/$',
        builder.AddSubAppDef.as_view(),
        name="builder-add-subapp"
    ),
    url(r'^builder/subform/change/$',
        builder.ChangeSubAppDef.as_view(),
        name="builder-change-subapp"
    ),
    url(r'^builder/?$',
        builder.Index.as_view(),
        name="builder-index"
    ),

    # File static server view
    url(r'^storage/(?P<ad_slug>[-\w]+)/(?P<app>\d+)/(?P<field_slug>[-\w]+)/(?P<file>.+)$',
        'formunculous.views.apply.file_view',
        name = "storage_view"
    )
)
