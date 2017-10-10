from django.conf.urls import url
from django.contrib.auth.views import login, LogoutView

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^question/(?P<slug>[^\.]+)/$', views.detail, name='detail'),
    url(r'^question/(?P<slug>[^\.]+)/submit$', views.submit, name='submit'),
    url(r'^question/(?P<slug>[^\.]+)/result/(?P<attempt_id>[-0-9]+)$', views.result, name='result'),
    url(r'^profile/(?P<username>[a-zA-Z0-9]+)/$', views.profile, name='profile'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', LogoutView.as_view(next_page='/login'), name='logout'),
]