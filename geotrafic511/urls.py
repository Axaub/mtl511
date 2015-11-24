from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from .views import simple_index_page

urlpatterns = [
    url(r'^api/', include('open511_server.urls')),

    url(r'^carte/', include('django_open511_ui.urls')),
    url(r'^accounts/', include('django_open511_ui.auth_urls')),

    url(r'^admin/', admin.site.urls),

    url(r'^$', simple_index_page),
]

if getattr(settings, 'URL_PREFIX'):
    urlpatterns = url('^' + settings.URL_PREFIX, include(urlpatterns))
