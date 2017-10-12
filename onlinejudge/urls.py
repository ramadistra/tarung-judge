from django.conf.urls import url
from django.contrib.auth.views import login, logout

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^activity$', views.activity, name='activity'),
    url(r'^scoreboard$', views.leaderboard, name='leaderboard'),
    url(r'^question/(?P<slug>[^\.]+)/$', views.detail, name='detail'),
    url(r'^question/(?P<slug>[^\.]+)/submit$', views.submit, name='submit'),
    url(r'^question/(?P<slug>[^\.]+)/judger-offline$', views.judger_offline, name='judger-offline'),
    url(r'^question/(?P<slug>[^\.]+)/result/(?P<attempt_id>[-0-9]+)$', views.result, name='result'),
    url(r'^profile/(?P<username>[a-zA-Z0-9._]+)/$', views.profile, name='profile'),
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, name='logout'),
]