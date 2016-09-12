"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^list_activity/$', views.voterListsActivity, name='voter_lists_activity'),
    url(r'^manage/$', views.voterLists, name='voter_lists'),
]
