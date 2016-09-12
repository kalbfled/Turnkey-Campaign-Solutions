"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.models import Address
from campaign.forms import CampaignForm
from campaign.models import Campaign, CampaignsToVoters, Office, PoliticalParty
from datetime import date
from django.test import TestCase
from tcsuser.models import TcsUser
from voter.models import Voter, VoterList

class CampaignTests(TestCase):
    """Tests for the campaign.models.Campaign."""
    fixtures = ['addresses.json', 'offices.json', 'politicalparties.json', 'voterdialingtesting.json']

    def setUp(self):
        """
        Store or create additional instances necessary for testing:
            TcsUser x2
            PoliticalParty x2
            Office x1 (President of the United States)
            Address x1
            Campaign x2
            VoterList x2
        Check the counts of the voters in the fixture, and relate all voters to both camapaigns.
        """
        super(CampaignTests, self).setUp()

        # Create 2 active users
        self.user1 = TcsUser.objects.create_user('test@tcs.com', 'Pa33word44')
        self.user1.is_active = True
        self.user1.save()

        self.user2 = TcsUser.objects.create_user('Neazy@tcs.com', 'Pa33word44')
        self.user2.is_active = True
        self.user2.save()

        # Store 1 office and 2 competing political parties
        self.potus = Office.objects.get(country='US', level='F', title='President')
        self.dem = PoliticalParty.objects.get(country='US', title='Democratic')
        self.rep = PoliticalParty.objects.get(country='US', title='Republican')

        # Store an address to use for creating campaigns
        address = Address.objects.first()

        # Create 2 competing presidential campaigns

        # An active general election Democratic campaign for President of the United States
        self.campaign1 = Campaign.objects.create(
            owner=self.user1,
            address=address,
            name='Sprout for POTUS',
            is_active=True,
            is_electoral=True,
            election_date=date.today(),
            office=self.potus,
            district=None,
            party=self.dem,
        )

        # An inactive primary election Republican campaign for President of the United States
        self.campaign2 = Campaign.objects.create(
            owner=self.user2,
            address=address,
            name='Slugworth for President',
            is_electoral=True,
            election_date=date.today(),
            office=self.potus,
            district=None,
            party=self.rep,
        )

        # Create two voter lists.  This is necessary to relate voters to campaigns.
        voter_list1 = VoterList.objects.create(
            dump_date=date.today(),
            campaign=self.campaign1,
            file_name='/dev/null',
        )

        voter_list2 = VoterList.objects.create(
            dump_date=date.today(),
            campaign=self.campaign1,
            file_name='/dev/null',
        )

        # Make sure the fixture voterdialingtesting.json contains the expected number of voters
        self.assertEqual(Voter.objects.count(), 9)        # 9 voters total
        democratic_voters = Voter.objects.filter(affiliation=self.dem)
        republican_voters = Voter.objects.filter(affiliation=self.rep)
        self.assertEqual(democratic_voters.count(), 4)    # 4 Democratic voters
        self.assertEqual(republican_voters.count(), 5)    # 5 Republican voters

        # Relate Democratic voters to 'Sprout for Potus' and Republican voters to 'Slugworth for President'
        relations = map(lambda voter: CampaignsToVoters(campaign=self.campaign1, voter=voter, voter_list=voter_list1),
            democratic_voters)
        CampaignsToVoters.objects.bulk_create(relations)
        relations = map(lambda voter: CampaignsToVoters(campaign=self.campaign2, voter=voter, voter_list=voter_list2),
            republican_voters)
        CampaignsToVoters.objects.bulk_create(relations)
        self.assertEqual(CampaignsToVoters.objects.count(), 9)

    def testAuthorizes(self):
        """Test the Campaign model's 'authorizes' method."""
        self.assertTrue(self.campaign1.authorizes(self.user1))
        self.assertFalse(self.campaign1.authorizes(self.user2))
        # TODO - This is not very comprehensive; what about non-owners?

    def testWorkersMethods(self):
        """Test the Campaign model's methods addProspect, addWorker, and addToBlacklist."""
        # Should not be able to add a campaign's owner to any of the ManyToMany fields
        self.assertIsNone(self.campaign1.addProspect(self.user1))
        self.assertIsNone(self.campaign1.addWorker(self.user1))
        self.assertIsNone(self.campaign1.addToBlacklist(self.user1))

        # Should be able to add a non-owner as a worker
        self.assertIsNotNone(self.campaign1.addWorker(self.user2))

        # Current workers should not be added as prospects
        self.assertIsNone(self.campaign1.addProspect(self.user2))

        # Blacklisted users shoud be removed from the list of prospects
        self.assertIsNotNone(self.campaign1.addToBlacklist(self.user2))
        self.assertEqual(self.campaign1.prospects.count(), 0)

        # Should not be able to add a blacklisted user as a prospect
        self.assertIsNone(self.campaign1.addProspect(self.user2))

        # Should be able to add a blacklisted user as a worker
        self.assertIsNotNone(self.campaign1.addWorker(self.user2))

    def testGetVotersToContact(self):
        """
        Test the Campaign model's getVotersToContact method, which should return active constituent voters
        who have not been contacted since the last election and have not been served to a supporter in the
        last two days.
        """
        voters1 = self.campaign1.getVotersToContact()
        voters2 = self.campaign2.getVotersToContact()
        self.assertEqual(voters1.count(), 4)
        self.assertEqual(voters1.filter(pk__in=[7,8,9,10]).count(), 4)
        self.assertEqual(voters2.count(), 5)
        self.assertEqual(voters2.filter(pk__in=[2,3,4,5,6]).count(), 5)
        
        # Inactive voters should not be served
        Voter.objects.filter(pk=7).update(is_active=False)
        self.assertFalse(self.campaign1.getVotersToContact().filter(pk=7).exists())

        # The method should not return voters contacted by the campaign within the last two years
        CampaignsToVoters.objects.filter(campaign=self.campaign1).update(last_contacted=date.today())
        self.assertFalse(self.campaign1.getVotersToContact().exists())

        # The method should not return voters served to campaign volunteers within the last two days
        CampaignsToVoters.objects.filter(campaign=self.campaign2).update(last_served=date.today())
        self.assertFalse(self.campaign2.getVotersToContact().exists())

    def testGetVotersToDial(self):
        """
        Test the Campaign model's getVotersToDial method, which should filter the query set returned by the
        method getVotersToContact voters without valid phone contact information.  Phone contact information
        is invalid if both phone_numberX fields are blank or if no available phone number has less than two
        reports of being invalid.
        """
        voters1 = self.campaign1.getVotersToDial()
        voters2 = self.campaign2.getVotersToDial()

        # Voters without any phone contact information should not be served
        self.assertEqual(voters2.count(), 1)
        self.assertFalse(voters2.filter(pk__in=[3,4,5,6]).exists())

        # Exclude voters with invalid phone contact information
        self.assertTrue(voters1.filter(pk=7).exists())  # phone_number1 reported as incorrect, but phone_number2 is available
        self.assertFalse(voters1.filter(pk=8).exists()) # Two numbers; both reported as incorrect
        self.assertEqual(voters1.count(), 3)

class CampaignFormTests(TestCase):
    """Tests for the campaign.forms.CampaignForm."""
    fixtures = ['offices.json', 'politicalparties.json']

    def setUp(self):
        """Store one Office instance and one PoliticalParty instance."""
        super(CampaignFormTests, self).setUp()
        self.office = Office.objects.first()
        self.party = PoliticalParty.objects.first()

    def testIsElectoralInterlocks(self):
        """
        If is_electoral is True, the election_date field cannot be blank.  'office'
        can be blank to indicate 'other'.
        """
        data = {
            'name': 'Sprout for POTUS',
            'is_active': True,
            'is_electoral': True,           # If this is True . . .
            'election_date': date.today(),  #     Required
            'office': self.office.pk,
            'district': None,
            'party': self.party.pk,
            'phone_number': '555-555-5555',
        }
        self.assertTrue(CampaignForm(data).is_valid())

        # Electoral campaigns must include election_date
        data['election_date'] = None
        self.assertFalse(CampaignForm(data).is_valid()) # Omitting election_date
        data['election_date'] = date.today()
        data['office'] = None
        self.assertTrue(CampaignForm(data).is_valid()) # Omitting office

        # Non-electoral campaigns may omit election_date
        data['is_electoral'] = False
        self.assertTrue(CampaignForm(data).is_valid())  # Omitting office
        data['office'] = self.office.pk
        data['election_date'] = None
        self.assertTrue(CampaignForm(data).is_valid())  # Omitting election_date
        data['office'] = None
        self.assertTrue(CampaignForm(data).is_valid())  # Omitting both
