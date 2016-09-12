"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from campaign.models import Campaign
from tastypie.authentication import BasicAuthentication, MultiAuthentication, SessionAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.resources import ModelResource
from tastypie.throttle import CacheThrottle

class CampaignAuthorization(ReadOnlyAuthorization):
    """Return a list of campaigns the user owns or for which the user works."""
    def read_list(self, object_list, bundle):
        """
        http://django-tastypie.readthedocs.org/en/latest/authorization.html#the-authorization-api
        https://stackoverflow.com/questions/431628/how-to-combine-2-or-more-querysets-in-a-django-view#434755
        
        Note that logical ORing of results from different tables can produce duplicates.
        """
        campaigns = bundle.request.user.works_for.filter(is_active=True) | Campaign.objects.filter(owner=bundle.request.user, is_active=True)
        return campaigns.distinct()

class CampaignResource(ModelResource):
    """Use this resource to return a list of campaigns the user owns or for which the user works."""
    class Meta:
        queryset = Campaign.objects.filter(is_active=True)
        max_limit = 20
        authentication = MultiAuthentication(SessionAuthentication(), BasicAuthentication())
        authorization = CampaignAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = []
        include_resource_uri = False
        fields = ['id', 'name']
        throttling = CacheThrottle(throttle_at=1, timeframe=60) # 1 request every minute
