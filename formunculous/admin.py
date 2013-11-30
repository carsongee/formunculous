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

from django.conf.urls import patterns, url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.functional import lazy
from django.views.generic import RedirectView

from formunculous.models import Form

reverse_lazy = lazy(reverse, unicode)

class FormAdmin(admin.ModelAdmin):
    """
       This "Admin Model" is used to shim proper URLs for administering
       formunculous.
    """

    def get_urls(self):
        urls = patterns('',
                        url(r'^$',
                            RedirectView.as_view(url=reverse_lazy('builder-index')),
                            name="formunculous_applicationdefinition_changelist",
                        ),
                        
                        url(r'^add/$',
                            RedirectView.as_view(url=reverse_lazy('builder-add-ad')),
                            name="formunculous_applicationdefinition_add",
                        )
                    )
        return urls
                        
admin.site.register(Form, FormAdmin)
