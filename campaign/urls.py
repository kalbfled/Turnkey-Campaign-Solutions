"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.campaignSearch, name='campaign_search'),
    url(r'^create/$', views.campaignCreate, name='campaign_create'),
    url(r'^(?P<campaign_id>\d+)/add/(?P<user_id>\d+)/$', views.campaignAdd, name='campaign_add'),
    url(r'^(?P<campaign_id>\d+)/blacklist/(?P<user_id>\d+)/$', views.campaignBlacklist, name='campaign_blacklist'),
    url(r'^(?P<campaign_id>\d+)/edit/$', views.campaignEdit, name='campaign_edit'),
    url(r'^(?P<campaign_id>\d+)/join/$', views.campaignJoin, name='campaign_join'),
    url(r'^(?P<campaign_id>\d+)/leave/$', views.campaignLeave, name='campaign_leave'),
    url(r'^(?P<campaign_id>\d+)/manage/$', views.campaignManage, name='campaign_manage'),
]
