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

from django.contrib import admin
from django.conf.urls.defaults import *
from formunculous.models import Form
from django.utils.functional import lazy
from django.core.urlresolvers import reverse

reverse_lazy = lazy(reverse, unicode)

class FormAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = patterns('django.views.generic.simple',
                        url(r'^$', 'redirect_to', 
                            {'url': reverse_lazy('builder-index')},
                            name="formunculous_applicationdefinition_changelist"),
                        
                        url(r'^add/$', 'redirect_to', 
                            {'url': reverse_lazy('builder-add-ad')},
                            name="formunculous_applicationdefinition_add"),
                        )
        return urls
                        
admin.site.register(Form, FormAdmin)
