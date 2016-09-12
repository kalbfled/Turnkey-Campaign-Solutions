"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.models import Address
from campaign.models import Campaign, Office, PoliticalParty
from datetime import date
from django.test import TestCase
from tcsuser.models import TcsUser
from time import sleep
from voter.models import Voter, VoterList

class VoterContactTests(TestCase):
    pass
    
class VoterListTests(TestCase):
    """Tests for voter.model.VoterList."""
    fixtures = ['addresses.json', 'offices.json', 'politicalparties.json']

    def setUp(self):
        """
        Create a VoterList instance.  This requires creating multiple other model instances.
        """
        super(VoterListTests, self).setUp()

        # Create an active user
        self.user = TcsUser.objects.create_user('test@tcs.com', 'Pa33word44')
        self.user.is_active = True
        self.user.save()

        # Store 1 office and 2 political parties
        self.potus = Office.objects.get(country='US', level='F', title='President')
        self.dem = PoliticalParty.objects.get(country='US', title='Democratic')
        self.rep = PoliticalParty.objects.get(country='US', title='Republican')

        # Store an address to use for creating campaigns
        address = Address.objects.first()

        # An active general election Democratic campaign for President of the United States
        self.campaign = Campaign.objects.create(
            owner=self.user,
            address=address,
            name='Sprout for POTUS',
            is_active=True,
            is_electoral=True,
            election_date=date.today(),
            office=self.potus,
            district=None,
            party=self.dem,
        )

    def testSignals(self):
        """
        Creating a new VoterList instance should trigger a listener that parses the list and adds new
        voters to the Voter table.

        The test list contains 11 voters with 1 duplicate (name and address) and 1 invalid voter (no name).
        The duplicated name actually appears three times, but the address is different in the third instance,
        which should be treated as a different voter.  This latter case also has no registration date,
        but that should not break anything.  One voter has no registration ID number, which also should not
        cause a problem.
        """
        voter_list = VoterList.objects.create(
            dump_date=date.today(),
            campaign=self.campaign,
            file_name='voter/voterlist.txt'
        )
        self.assertEqual(VoterList.objects.count(), 1)
        self.assertEqual(Voter.objects.count(), 9)
        
        # Make sure the e-mail column, which is between two ignored columns, is recognized
        self.assertEqual(Voter.objects.exclude(email='').count(), 2)

        # Voters without required information should not be saved.  The following voter has no first or last
        # name information.
        self.assertFalse(Voter.objects.filter(address__street='6483 S 1000 W').exists())

        # The following registrar_id is in the input file 3 times.  The first instance is valid and contains
        # text in columns that should be ignored.  The second instance is an exact duplicate of the first
        # instance; ignore it.  The third instance has a different street address and omits all the optional
        # fields.  Add it.
        self.assertEqual(Voter.objects.filter(registrar_id='{4E061E97-91EE-4987-B8B3-580688B817BB}').count(), 2)
        self.assertTrue(Voter.objects.filter(address__street='59 S Byron St').exists())

        # There are 8 unique addresses in the test list; 1 is for an invalid voter.
        # addresses.json contains 11 addresses (which are not checked for duplicates)
        self.assertEqual(Address.objects.count(), 18)

        # Test party affiliations
        self.assertEqual(Voter.objects.filter(affiliation=self.rep).count(), 4) # Republicans
        # There are 4 Democrats in the list, but one is invalid
        self.assertEqual(Voter.objects.filter(affiliation=self.dem).count(), 3) # Democrats
        self.assertIsNone(Voter.objects.get(last_name='Duckie').affiliation)    # Ignore the Smurf Party
        self.assertEqual(Voter.objects.filter(affiliation=None).count(), 2)     # Independent or unknown affiliation

        # The voters should be related to the campaign that created them
        self.assertEqual(self.campaign.voters.count(), 9)

        self.assertEqual(voter_list.processed, 'Imported 9 of 11 voters.  1 duplicates.  1 bad format.')
