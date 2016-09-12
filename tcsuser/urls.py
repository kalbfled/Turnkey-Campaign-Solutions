"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^activate/(\S+)/$', views.tcsuserActivate, name='tcsuser_activate'),
    url(r'^edit/$', views.tcsuserEdit, name='tcsuser_edit'),
    url(r'^register/$', views.tcsuserRegister, name='tcsuser_register'),
]
