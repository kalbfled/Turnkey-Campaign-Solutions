"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.models import Address
from datetime import date, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django_countries.fields import CountryField

class Office(models.Model):
    """
    This models stores the names of elected offices sought through elections.  Rows should not specify districts.
    For example, 'U.S. House of Representatives,' and not 'IL-10.'
    """
    country = CountryField()
    level = models.CharField(max_length=1, choices=(('F', 'Federal'), ('S', 'State, province, or territory'), ('O', 'Other')))
    title = models.CharField(max_length=100)

    def __unicode__(self):
        return self.title
        
class PoliticalParty(models.Model):
    """This models stores the names of political parties in different countries."""
    country = CountryField()
    title = models.CharField(max_length=100)

    def __unicode__(self):
        return self.title

class Campaign(models.Model):
    """
    Every campaign has an owner, multiple workers, relevant voters, and contact information.
    Active campaigns are discoverable by prospective volunteers.

    workers - Users who may query a campaign's voter list and make intelligence reports
    prospects - Users requesting to become workers
    blacklist - User who are not workers and who may not request to become workers
    """
    # Every campaign has a unique owner who can only own one campaign.
    # TODO - Make the owner editable.  The choices should be existing workers who do not already own a campaign.
#    owner = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='campaign', limit_choices_to={})
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='campaign')
    address = models.ForeignKey(Address)
    # Don't make the name field unique.  There could be many "Smith for Congress" campaigns.
    name = models.CharField('Campaign name', max_length=100, help_text='As you want it to appear to volunteers')
    phone_number = models.CharField(max_length=15)  # TODO - Country specific validation
    is_active = models.BooleanField('Accepting volunteers, reports about voters, etc.?', help_text='(yes)', default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    workers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='works_for', editable=False)
    prospects = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='prospect_for', editable=False)
    blacklist = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='blacklisted', editable=False)
    voters = models.ManyToManyField('voter.Voter', through='CampaignsToVoters', editable=False)  # Avoid the circular import error

    # These fields are specific to electoral campaigns
    is_electoral = models.BooleanField('Are you trying to win an election or referendum?',
        help_text='(yes)', default=False)
    election_date = models.DateField(help_text='yyyy-mm-dd', null=True, blank=True)
    office = models.ForeignKey(Office, help_text='Leave blank for "other."', null=True, blank=True)
    district = models.PositiveSmallIntegerField(null=True, blank=True, help_text='Leave blank for state-wide and federal elections.')
    # TODO - limit choices by country
    party = models.ForeignKey(PoliticalParty, null=True, blank=True, help_text='Leave blank for independent campaigns.')

    def addProspect(self, user):
        """
        Add a user to 'prospects' unless the user is the campaign owner or is already linked
        to 'workers', 'prospects', or 'blacklist'.  Also decline to add prospects when the
        campaign is not active.

        user - A TcsUser instance to link to 'prospects'
        """
        if self.is_active and (user != self.owner) and not self.prospects.filter(pk=user.id).exists() \
                and not self.workers.filter(pk=user.id) and not self.blacklist.filter(pk=user.id).exists():
            self.prospects.add(user)
            return self
        return None

    def addToBlacklist(self, user):
        """
        Remove the user from the lists of workers and prospects, if applicable, and add
        the user to the blacklist.  Note that adding somebody as a worker removes the person
        from the blacklist.

        user - A TcsUser instance to link to the blacklist
        """
        if (user != self.owner) and not self.blacklist.filter(pk=user.id).exists():
            self.blacklist.add(user)
            if self.prospects.filter(pk=user.id).exists():
                self.prospects.remove(user)
            if self.workers.filter(pk=user.id).exists():
                self.workers.remove(user)
            return self
        return None

    def addWorker(self, user):
        """
        Remove the user from 'prospects' and 'blacklist', if applicable, and add the user to
        'workers'.  Note that adding somebody as a worker removes the person from the blacklist.

        user - A TcsUser instance to link to workers
        """
        if (user != self.owner) and not self.workers.filter(pk=user.id).exists():
            self.workers.add(user)
            if self.prospects.filter(pk=user.id).exists():
                self.prospects.remove(user)
            if self.blacklist.filter(pk=user.id).exists():
                self.blacklist.remove(user)
            return self
        return None

    def authorizes(self, user):
        """
        Return True if the campaign authorizes the user to provide data to the campaign.  This
        is the case if the user owns or works for the campaign.  Otherwise, return False.
        """
        return self.owner == user or self.workers.filter(pk=user.id).exists()

    def getOwnerOptions(self):
        """Return campaign workers who do not already own a campaign."""
        # TODO
        return self.workers.all()

    def getVotersToContact(self):
        """
        Return active constituent voters who have not been contacted since the last election and
        have not been served to a supporter in the last two days.  Don't limit the size of the
        result set here; let APIs do that.
        """
        two_days_ago = date.today() - timedelta(2)
        year_ago = date.today() - timedelta(365)
        return self.voters.filter(
            Q(campaignstovoters__last_served=None) | Q(campaignstovoters__last_served__lt=two_days_ago),
            Q(campaignstovoters__last_contacted=None) | Q(campaignstovoters__last_contacted__lt=year_ago),
            campaignstovoters__is_active=True,
            is_active=True)

    def getVotersToDial(self):
        """
        Return active constituent voters with valid phone contact information who have not been contacted
        since the last election.  Don't limit the size of the result set here; let APIs do that.
        """
        return self.getVotersToContact().exclude(
            (Q(phone_number1='') | Q(wrong_phone_number1__gt=1)),
            (Q(phone_number2='') | Q(wrong_phone_number2__gt=1)))

    def getVotersDoorToDoor(self, latitude, longitude):
        """
        Return active constituent voters in proximity to given latitude and longitude coordinates.  (Database
        contrainsts require all rows in the voters table to have valid address information.)  Don't limit the
        size of the result set here; let APIs do that.
        """
        pass

    def removeWorker(self, user):
        """
        Remove the user from 'workers' or 'prospects', if applicable.

        user - A TcsUser instance to remove from workers
        """
        if user == self.owner:
            return None
        # Without these queries, there's no way to tell if anything actually gets removed.
        # Calling remove() on a user that is not in the set does not raise an error.
        if self.workers.filter(pk=user.id).exists():
            self.workers.remove(user)
            return self
        if self.prospects.filter(pk=user.id).exists():
            self.prospects.remove(user)
            return self
        return None

    def voterContactCount(self, user):
        """Return the number of voters a user has contacted for the campaign."""
        return self.votercontact_set.filter(user=user).count()

    def __unicode__(self):
        return self.name

class CampaignsToVoters(models.Model):
    """
    This is an intermediate table for the Campaign-to-Voter many-to-many field, 'voters'.  It keeps
    track of the last time a given campaign contacted a voter and the last time the server sent
    a voter's contact information to a campaign supporter.
    """
    campaign = models.ForeignKey(Campaign)
    voter = models.ForeignKey('voter.Voter')
    voter_list = models.ForeignKey('voter.VoterList')
    last_contacted = models.DateField(null=True, default=None)
    last_served = models.DateField(null=True, default=None)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return 'id={0}, campaign_id={1}, voter_id={2}, list_id={3}'.format(self.pk, self.campaign.pk, self.voter.pk, self.voter_list.pk)
