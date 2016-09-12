"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.models import Address
from campaign.models import Campaign, PoliticalParty
from datetime import date
from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from os import makedirs
import os.path

class ContactMethod(models.Model):
    """Means to contact a voter. (i.e. phone, in-person, e-mail, etc.)"""
    method = models.CharField(max_length=20)

    def __unicode__(self):
        return self.method

class Issue(models.Model):
    """
    A table of political issues about which voters might have strong opinions.
    Examples: abortion, 2nd ammendment, unions, etc.  The issue should be phrased in such
    a manner that voters can be said simply to "support" or "oppose" the issue.

    The rows in this table serve as choices for fields in the intelligence_report field of a
    VoterContact instance.  Some issues are specific to a country.  General issues have a blank
    value for the country field.

    Set the field 'is_active' to False to prevent the issue from being served via API GET
    requests.  Deleting rows from the table is not desirable because intelligence reports
    make reference to Issue instances.
    """
    country = CountryField(blank=True, default='')
    issue = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.issue

class Voter(models.Model):
    """A registered voter."""
    # Who
    first_name = models.CharField(max_length=30, help_text='Include middle name or initial')
    last_name = models.CharField(max_length=30)
    dob = models.DateField('Date of birth', help_text='yyyy-mm-dd', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female')), blank=True)
    affiliation = models.ForeignKey(PoliticalParty, null=True, blank=True)  # Registered party affiliation, if any
    is_active = models.BooleanField(default=True)
    registration_date = models.DateField(help_text='When did this person register to vote?', null=True, blank=True)

    registrar_id = models.CharField(max_length=100, help_text='Unique Id assigned by the voter registration authority',
        blank=True, default='')
    dump_date = models.DateField(help_text='When did the registering authority dump this voter data?')
    
    # Contact information
    address = models.ForeignKey(Address)
    phone_number1 = models.CharField(max_length=12, blank=True)
    phone_number2 = models.CharField(max_length=12, blank=True)
    email = models.EmailField('e-mail', max_length=254, blank=True)

    # These fields should be reset to zero as appropriate after a voter contact event.  If all the counts cross a
    # threshold, the voter should be made inactive.
    wrong_address = models.PositiveSmallIntegerField(default=0, editable=False)
    wrong_phone_number1 = models.PositiveSmallIntegerField(default=0, editable=False)
    wrong_phone_number2 = models.PositiveSmallIntegerField(default=0, editable=False)

    def __unicode__(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

class VoterContact(models.Model):
    """
    A voter contact event.  A TcsUser contacts a Voter on behalf of a Campaign (or more than one).
    This model also captures information about a voter's preferences--an Intelligence Report--in
    a custom json format that is not part of this model definition.
    """
    voter = models.ForeignKey(Voter, editable=False)
    campaigns = models.ManyToManyField(Campaign, editable=False)
    contact_datetime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False)                # The campaign worker who made contact
    method = models.ForeignKey(ContactMethod)                                         # How the campaign worker made contact
    intelligence_report = models.TextField(max_length=1000, blank=True, default='""') # 1,000 characters is about 2 paragraphs
    # TODO - IRs might be much longer than 1,000 characters if they are encrypted

    def __unicode__(self):
        return '{0} by {1}'.format(self.voter, self.user)

def getUploadPath(instance, filename):
    """https://docs.djangoproject.com/en/1.8/ref/models/fields/#filefield"""
    path = '{0}{1}/'.format(settings.VOTER_LISTS_ROOT, instance.campaign.id)
    if not os.path.exists(path):
        # Create path folders if necessary
        makedirs(path)
    return '{0}{1}'.format(path, filename)

class VoterList(models.Model):
    """
    A list of voter data uploaded by a campaign.  The voters in the list are assumed to be
    relevant for that campaign.
    """
    dump_date = models.DateField('When did the voter registration authority give you this data?', help_text='yyyy-mm-dd')
    campaign = models.ForeignKey(Campaign, editable=False)
    upload_datetime = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField('Contact voters in this list?', default=True)
    file_name = models.FileField(upload_to=getUploadPath)
    processed = models.CharField(max_length=100, default='No', editable=False) # Status of processing the list

    def getShortFileName(self):
        """Return file_name without the path or extension."""
        return os.path.splitext(os.path.basename(self.file_name.url))[0]

    def __unicode__(self):
        return self.file_name
