"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.api import AddressResource
from campaign.api import CampaignResource
from campaign.models import Campaign, CampaignsToVoters
from datetime import date
from django.db.models import Q
from tastypie import fields
from tastypie.authentication import BasicAuthentication, MultiAuthentication, SessionAuthentication
from tastypie.authorization import Authorization, ReadOnlyAuthorization
from tastypie.exceptions import BadRequest
from tastypie.resources import ModelResource
from tastypie.throttle import CacheThrottle
from voter.models import ContactMethod, Issue, Voter, VoterContact

class ContactMethodResource(ModelResource):
    """This resource exists solely to embed in VoterContactResource.  It does not need an endpoint."""
    class Meta:
        queryset = ContactMethod.objects.all()

class IssueAuthorization(ReadOnlyAuthorization):
    """
    An authenticated user should only receive issues relevant to her country of residence
    and issues applicable to any country.  This could be accomplished with filtering using
    GET parameters, but client applications don't know a user's address.
    """
    def read_list(self, object_list, bundle):
        """
        http://django-tastypie.readthedocs.org/en/latest/authorization.html#the-authorization-api
        """
        return object_list.filter(Q(country=bundle.request.user.profile.address.country) | Q(country='')).order_by('issue')

class IssueResource(ModelResource):
    class Meta:
        queryset = Issue.objects.filter(is_active=True)
        authentication = MultiAuthentication(SessionAuthentication(), BasicAuthentication())
        authorization = IssueAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = []
        include_resource_uri = False
        fields = ['id', 'issue']
        limit = 100
        max_limit = None
        throttling = CacheThrottle(throttle_at=1, timeframe=604800) # 1 request every week

class VoterAuthorization(Authorization):
    """
    An authenticated user should only have access to voters who are constituents of campaigns
    that authorize the user to contact voters on their behalf.

    http://django-tastypie.readthedocs.org/en/latest/authorization.html#the-authorization-api
    """
    def read_list(self, object_list, bundle):
        """
        Return up to 20 voters relevant to up to 5 campaigns, passed as a GET parameter, for which
        the user is authorized to contact voters.  Only consider the first five campaign is.  The
        GET parameter is a comma-separated list of integers.  For example, "?campaign_id=1,2,3".
        """
        try:
            campaign_ids = map(int, bundle.request.GET.__getitem__('campaign_id').split(','))
        except KeyError:
            raise BadRequest("Invalid campaign_id")
        campaigns = Campaign.objects.filter(pk__in=campaign_ids, is_active=True)
        # The following filter converts 'campaigns' from a QuerySet to a list of Campaign instances
        campaigns = [campaign for campaign in campaigns if campaign.authorizes(bundle.request.user)][:5]
        if campaigns:
            # TODO - This assumes contact by telephone.  Later, include a method of contact GET parameter.
            # The following reduce operation produces a QuerySet
            voters = reduce(lambda voters_intersection, campaign: voters_intersection & campaign.getVotersToDial(),
                frozenset(campaigns), object_list)[:20:1] # Note the step
                
            # https://docs.djangoproject.com/en/1.8/ref/models/querysets/#when-querysets-are-evaluated
            # Using the step component in the slice notation above forces evaluation of the query.
            # Without this, updating the many-to-many field below empties the expected result set.

            # Update the 'last_served' field of campaign.models.CampaignsToVoters
            # TODO - Uncomment this update for production.
#            CampaignsToVoters.objects.filter(
#               campaign__in=campaigns,
#                voter__in=voters
#            ).update(last_served=date.today())
            return voters
        return []

    def create_detail(self, object_list, bundle):
        """The user should not be able to create a new Voter with PATCH."""
        return False

    def update_detail(self, object_list, bundle):
        """
        First, ensure the user is not trying to create a new resource with a PUT request,
        which is permissible according to VoterResource.detail_allowed_methods because it
        is necessary to process PATCH requests to a list endpoint.

        Return True if the bundled Voter object is a constituent of any active campaign
        that authorizes the user.  Otherwise, return False.
        """
        if bundle.request.method == 'PUT':
            return False
        relevant_campaigns = bundle.obj.campaign_set.filter(is_active=True)
        for campaign in relevant_campaigns:
            if campaign.authorizes(bundle.request.user):
                return True
        return False

class VoterResource(ModelResource):
    """
    Use this resource to return voters relevant to a specific campaign for which the
    authenticated user works.  Also use it to update voters when users indicate
    incorrect contact information by "flagging" a phone number or address.

    For testing the PATCH functionality using the credentials dave@purdone.com:Pa33word44 with cURL:
    curl --dump-header - -H "Content-Type: application/json" -H "Authorization: Basic ZGF2ZUBwdXJkb25lLmNvbTpQYTMzd29yZDQ0" -X PATCH --data '{"objects":[{"resource_uri":"/api/v1/voter/1/","phone_number1":""},{"resource_uri":"/api/v1/voter/7/","phone_number1":""}]}' http://localhost:8000/api/v1/voter/
    """
    # TODO - This assumes contact by telephone.  Contact door-to-door will require passing GPS coordinates
    # as GET parameters.  When multiple contact methods are supported, a GET parameter might be necessary.
    address = fields.ForeignKey(AddressResource, 'address', full=True) # 'True' to embed for child resource; not just a link

    class Meta:
        queryset = Voter.objects.filter(is_active=True)
        authentication = MultiAuthentication(SessionAuthentication(), BasicAuthentication())
        authorization = VoterAuthorization() # Note that GET requires campaign IDs as GET parameters
        list_allowed_methods = ['get', 'patch']
        detail_allowed_methods = ['put']
        fields = ['id', 'first_name', 'last_name', 'gender', 'phone_number1', 'phone_number2', 'address']
        limit = 20
        max_limit = 20
        throttling = CacheThrottle(throttle_at=1, timeframe=1800) # 1 request every 30 minutes

    def hydrate(self, bundle):
        """
        A PATCH request to a list endpoint should be an update to report flagged contact information, and
        this is the only use case permitted by VoterAuthorization.  Therefore, bundle.obj should be
        prepopulated with the Voter instance of interest.  bundle.data should contain the same data as
        bundle.obj for fields not specified by the user.

        This method focuses on the fields 'phone_number1' and 'phone_number2'.  If these fields are set to
        the value "flagged," the course of action is to increment the object's associated 'wrong_xxx' field.
        """
        if bundle.data.get('phone_number1') == 'flagged':
            bundle.obj.wrong_phone_number1 += 1
            bundle.data['phone_number1'] = bundle.obj.phone_number1 # Don't override the stored phone number
        elif bundle.data.get('phone_number2') == 'flagged':
            bundle.obj.wrong_phone_number2 += 1
            bundle.data['phone_number2'] = bundle.obj.phone_number2 # Don't override the stored phone number
        else:
            raise BadRequest("Nothing to update.")
        return bundle

    # Disregard all user supplied data not related to wrong contact information

    def hydrate_address(self, bundle):
        bundle.data['address'] = bundle.obj.address
        return bundle

    def hydrate_first_name(self, bundle):
        bundle.data['first_name'] = bundle.obj.first_name
        return bundle

    def hydrate_gender(self, bundle):
        bundle.data['gender'] = bundle.obj.gender
        return bundle

    def hydrate_id(self, bundle):
        bundle.data['id'] = bundle.obj.id
        return bundle

    def hydrate_last_name(self, bundle):
        bundle.data['last_name'] = bundle.obj.last_name
        return bundle

class VoterContactAuthorization(Authorization):
    """
    Authorization subclass for VoterContactResource.
    http://django-tastypie.readthedocs.org/en/latest/authorization.html#the-authorization-api
    """
    def update_detail(self, object_list, bundle):
        """
        Don't let the user update an existing resource.  A PUT request is permissible according
        to VoterContactResource.detail_allowed_methods because it is required to process PATCH
        requests to a list endpoint.  PUT (detail) and PATCH (list) both call this method, but
        the latter only does so when the data contains 'resource_url'.
        """
        return False

class VoterContactResource(ModelResource):
    """
    Use this resource to return information about voters relevant to specific campaigns for which
    the authenticated user works.  Use the PATCH method to create new VoterContact objects in bulk.
    This, rather than POST, is appropriate because user client applications, like TCS Campaigner,
    return information to the server in batches.  It would be undesirable to make 20 consecutive
    POST requests from the client.

    http://django-tastypie.readthedocs.org/en/latest/resources.html#advanced-data-preparation
    https://django-tastypie.readthedocs.org/en/latest/interacting.html#bulk-operations

    For PATCH requests to work, the Tastypie documentation incorrectly states that detail methods
    must include 'patch', but the source code reveals that 'put' is required.

    For testing the PATCH functionality using cURL:
    curl --dump-header - -H "Content-Type: application/json" -H "Authorization: Basic <see below>" -X PATCH --data '{"objects":[{"method":1,"voter":2,"intelligence_report":"Neazy!"},{"method":1,"voter":4,"intelligence_report":"DC yall"}]}' http://localhost:8000/api/v1/votercontact/
        After "Basic," include the Base64 encoding for the string "<login>:<password>".  See the
        Wikipedia entry for "basic authentication" for an example.

    When 'intelligence_report' is given a JSON object instead of a string, it stores the object in a
    stringified format as desired.
    """
    method = fields.ForeignKey(ContactMethodResource, 'method')
    voter = fields.ForeignKey(VoterResource, 'voter')

    class Meta:
        queryset = VoterContact.objects.all()
        authentication = MultiAuthentication(SessionAuthentication(), BasicAuthentication())
        authorization = VoterContactAuthorization()
        list_allowed_methods = ['patch']
        detail_allowed_methods = ['put']
        include_resource_uri = False
        fields = ['intelligence_report']
#        throttling = CacheThrottle(throttle_at=1, timeframe=1800) # 1 request every 30 minutes TODO - Uncomment in production

    def hydrate(self, bundle):
        """
        The authenticated user should be the TcsUser instance related with the new VoterContact instance.
        """
        bundle.obj.user = bundle.request.user
        return bundle

    def hydrate_method(self, bundle):
        """The user data only provides an Id, but the framework requires a ContactMethod instance."""
        try:
            bundle.data['method'] = ContactMethod.objects.get(pk=bundle.data['method'])
        except (KeyError, ContactMethod.DoesNotExist):
            raise BadRequest("Invalid 'method' value")
        return bundle

    def hydrate_voter(self, bundle):
        """The user data only provides an Id, but the framework requires a Voter instance."""
        try:
            bundle.data['voter'] = Voter.objects.get(pk=bundle.data['voter'])
        except (KeyError, Voter.DoesNotExist):
            raise BadRequest("Invalid 'voter' value")
        return bundle

    def hydrate_m2m(self, bundle):
        """
        The new VoterContact instance should relate to active campaigns the associated user supports that have
        an interest in the particular voter.
        """
        # Compose a query set of campaigns the user supports.  These are campaigns the user owns or for which she works.
        bundle.data['campaigns'] = bundle.request.user.works_for.filter(is_active=True) | Campaign.objects.filter(owner=bundle.request.user, is_active=True)
        # Intersect the query set with campaigns interested in the voter related to the VoterContact instance.
        bundle.data['campaigns'] = bundle.data['campaigns'] & bundle.obj.voter.campaign_set.filter(is_active=True)
        return bundle

    def save_m2m(self, bundle):
        bundle.obj.campaigns.add(*bundle.data['campaigns'])
