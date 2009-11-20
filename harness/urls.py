from django.conf.urls.defaults import *
from django.conf import settings
import os

project_path = os.path.dirname(__file__)
app_path = os.path.normpath(project_path + '/..')
print('%s/formunculous/media/' % app_path)

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
urlpatterns = patterns('',)
if settings.SERVE_MEDIA:
    urlpatterns += patterns('',
    (r'^media/(.*)$', 'django.views.static.serve',
     {'document_root': '%s/formunculous/media/' % app_path, 'show_indexes': True}),)


urlpatterns += patterns('',
    (r'^', include('formunculous.urls')),
    # Example:
    # (r'^application/', include('application.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
