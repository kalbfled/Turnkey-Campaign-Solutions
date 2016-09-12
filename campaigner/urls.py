"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.campaignerDial, name='campaigner_dial'),
    url(r'^campaigns/$', views.campaignerCampaigns, name='campaigner_campaigns'),
    url(r'^IR/$', views.campaignerIR, name='campaigner_IR'),
]
