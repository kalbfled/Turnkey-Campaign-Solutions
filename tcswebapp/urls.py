"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from campaign.api import CampaignResource
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from tastypie.api import Api
from voter.api import IssueResource, VoterResource, VoterContactResource
from . import views

# This application uses the TastyPie add-on to implement a RESTful API.  For a list of
# endpoints, visit <domain root>/api/v1/.
v1_api = Api(api_name='v1')
v1_api.register(CampaignResource())
v1_api.register(IssueResource())
v1_api.register(VoterResource())
v1_api.register(VoterContactResource())

urlpatterns = [
    # These urls use built-in authentication views for logging in and out.
    url(r'^$', auth_views.login, {'template_name': 'tcswebapp/index.html'}, name='login'),
    url(r'^logout/$', auth_views.logout_then_login, name='logout_then_login'),

    # This is the main dashboard for logged-in users.
    url(r'^home/$', views.home, name='home'),

    # Include urls for applications.
    url(r'^api/', include(v1_api.urls)),
    url(r'^campaign/', include('campaign.urls')),
    url(r'^campaigner/', include('campaigner.urls')),
    url(r'^user/', include('tcsuser.urls')),
    url(r'^voter/', include('voter.urls')),
]
