"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.forms import AddressForm
from address.models import Address
from campaign.models import CampaignsToVoters, PoliticalParty
from csv import DictReader
from dateutil.parser import parse
from django.db.models.signals import post_save
from django.dispatch import receiver
from voter.forms import VoterForm
from voter.models import Voter, VoterContact, VoterList

@receiver(post_save, sender=VoterList)
def processVoterList(sender, created, instance, **kwargs):
    """
    For each valid voter in the uploaded list, add it to the Voter table, and make a many-to-many
    link to the campaign that uploaded the list.  Do not duplicate voters already in the table.
    Consider a voter a duplicate if a voter already exists with the same registrar_id in the same
    state.
    """
    if not created:
        return
    try:
        f = open(instance.file_name.url)
    except IOError:
        instance.processed = 'Could not open the file.'
        instance.is_active = False
        instance.save()
        return

    default_country = str(instance.campaign.address.country) # The relevant campaign's home country
    line_count = 0
    num_successes = 0
    num_duplicates = 0
    num_bad_format = 0
    new_voter_relations = [] # A list of new CampaignsToVoters instances to add in bulk after processing the list
    new_indexes = set([])    # Explained below

    reader = DictReader(f, delimiter='\t') # Assumes the first row contains column names.
    for voter in reader:
        line_count += 1

        # Must catch KeyError and ValueError.
        try:
            # Convert date strings to datetime.Date instances.  Failure to convert raises ValueError.
            if voter['registration_date']:
                voter['registration_date'] = parse(voter['registration_date']).date()

            if voter['dob']:
                voter['dob'] = parse(voter['dob']).date()

            # Voter political affiliations are a ForeignKey in the Voter model, but the user uploads
            # text.  Attempt to find the correct political party operating in the campaign's country.
            affiliation = voter['affiliation'].strip()
            if affiliation != '':
                try:
                    affiliation = PoliticalParty.objects.get(
                        country=default_country,
                        title__icontains=affiliation
                    ).pk
                except (PoliticalParty.DoesNotExist, PoliticalParty.MultipleObjectsReturned):
                    affiliation = None  # Ignore the ambiguous party information.

            voter_form = VoterForm({
                'first_name': voter['first_name'],
                'last_name': voter['last_name'],
                'dob': voter['dob'],
                'gender': voter['gender'],
                'affiliation': affiliation,             # This should be an integer primary key or None.
                'registration_date': voter['registration_date'],
                'registrar_id': voter['registrar_id'],
                'dump_date': instance.dump_date,
                'phone_number1': voter['phone_number1'],
                'phone_number2': voter['phone_number2'],
                'email': voter['email'],
            })

            # Use the default country if necessary.
            if voter['country'] == '':
                voter['country'] = default_country

            address_form = AddressForm({
                'street': voter['street'],
                'city': voter['city'],
                'state': voter['state'],
                'country': voter['country'],
                'postal_code': voter['postal_code'],
            })
        except (KeyError, ValueError):
            num_bad_format += 1     # Missing required data
            continue                # Move on to the next line in the input file.

        if voter_form.is_valid() and address_form.is_valid():
            # Is this voter already in the database?  Look for active voters with the same registrar_id, 
            # street address, country, and state.
            # TODO - Registrar IDs are stored as-is and matched case-insensitively.
            # Should I just lower/upper-case and match exact?  Should case matter?
            v = Voter.objects.filter(is_active=True, registrar_id__iexact=voter_form.cleaned_data['registrar_id'],
                address__street=address_form.cleaned_data['street'],
                address__country=address_form.cleaned_data['country'],
                address__state=address_form.cleaned_data['state']).first()
            if not v:
                # The voter is not in the database or is not active.  Add him or her.
                voter_form.instance.address = address_form.get_or_create()
                v = voter_form.save()

            # Relate the voter to the campaign that uploaded the current list, if applicable.
            # Two scenarios can raise an IntegrityError by duplicating a (campaign, voter)
            # combination in the database table Campaign.campaignstovoters:
            #   1) Duplicate voters are present in the new list.
            # This raises an error when creating the m2m relations after creating each new
            # voter.  Mitigate this by keeping track of voter indexes seen in the new list.
            #   2) The same campaign has already submitted a voter in another list.
            # Having multiple m2m relations associated with different lists is desirable,
            # but the framework does not support this.  Simply ignore voters already present
            # from another list.
            if v.pk not in new_indexes and not CampaignsToVoters.objects.filter(
                    campaign=instance.campaign, voter=v).exists():
                new_indexes.add(v.pk)
                new_voter_relations.append(CampaignsToVoters(campaign=instance.campaign, voter=v, voter_list=instance))
                num_successes += 1
            else:
                num_duplicates += 1
        else:
            num_bad_format += 1     # No required data missing, but the provided data is invalid.

    f.close()

    # Update the many-to-many relationship.
    CampaignsToVoters.objects.bulk_create(new_voter_relations)

    # Update the VoterList instance.
    instance.processed = 'Imported {0} of {1} voters.  {2} duplicates.  {3} bad format.'.format(
        num_successes, line_count, num_duplicates, num_bad_format)
    instance.is_active = (num_successes > 0)
    instance.save()

@receiver(post_save, sender=VoterContact)
def updateLastContacted(sender, created, instance, **kwargs):
    """
    After a user contacts a voter, record the date of the contact event in the campaigns-to-voters
    many-to-many table, campaign.models.CampaignsToVoters.  Note that this updates multiple rows if
    the voter is referenced in multiple voter lists.
    """
    if created:
        CampaignsToVoters.objects.filter(
            campaign__in=instance.campaigns.all(),
            voter=instance.voter
        ).update(last_contacted=instance.contact_datetime.date())

@receiver(post_save, sender=VoterList)
def updateVoterListActivity(sender, created, instance, **kwargs):
    """
    When a campaign owner changes the 'is_active' value of a VoterList instance, this listener
    updates the 'is_active' value of the rows in CampaignsToVoters associated with the affected
    lists.  The end goal is that the Voter API list endpoint will only serve to volunteers voters
    the campaign manager presently wants to contact.
    """
    if not created:
        CampaignsToVoters.objects.filter(
            voter_list=instance,
        ).update(is_active=instance.is_active)
