"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.models import Address
from tastypie.resources import ModelResource

class AddressResource(ModelResource):
    """
    This resource should not have an endpoint.  It exists to include address
    data in other resources, such as VoterResource.
    """
    class Meta:
        queryset = Address.objects.all()
        list_allowed_methods = []
        detail_allowed_methods = []
        include_resource_uri = False
        fields = ['city', 'state']
