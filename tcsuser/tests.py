"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.forms import AddressForm
from address.models import Address
from django.conf import settings
from django.core import mail
from django.core.signing import TimestampSigner
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from tcsuser.forms import TcsUserCreationForm, TcsUserProfileForm
from tcsuser.models import TcsUser, TcsUserProfile

def setUserData(obj):
    """
    This utility function sets a 'user_data' attribute on 'obj', an instance of TestCase.
    Multiple tests call this function to avoid code repition.
    """
    obj.user_data = {
        'email': 'test@TCS.com',
        'password': 'Pa33word44',
        'password2': 'Pa33word44',
    }
    obj.assertTrue(TcsUserCreationForm(obj.user_data).is_valid())

class TcsUserTests(TestCase):
    """Tests for the TcsUser model and listener."""

    def setUp(self):
        setUserData(self)

    def checkMail(self):
        """Verify that user creation triggers the listener, tcsuser.signals.SendActivationLink()."""
        self.assertEqual(len(mail.outbox), 1)      # Ensure only 1 message sent
        self.assertEqual(mail.outbox[0].subject, 'Activate your account')
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(mail.outbox[0].to, [self.user_data['email'].lower()])
        # A timestamped signature created here will have a different value that a timestamp created elsewhere,
        # so testing the link for an exact match is not possible.
        self.assertIn('activate', mail.outbox[0].body)

    def testActivationLink(self):
        """Ensure that following the activation link makes the TcsUser instance active."""
        user = TcsUser.objects.create_user(self.user_data['email'], self.user_data['password'])
        self.assertFalse(user.is_active) # The new registrant is inactivate
        usercode = TimestampSigner().sign(user.email)
        # User creation should trigger sending an activation e-mail via a listener
        self.checkMail()

        # This GET request should activate the new TcsUser instance.
        response = Client().get(reverse('tcsuser_activate', args=(usercode,)))
        user = TcsUser.objects.get(pk=user.id)  # Syncronize the variable with the database
        self.assertTrue(user.is_active)

class TcsUserCreationFormTests(TestCase):
    """This primarily tests e-mail and password validation."""

    def setUp(self):
        setUserData(self)

    def testTcsUserCreationForm(self):
        """Test the validation behavior using tcsuser.forms.TcsUserCreationForm."""

        # Test password validation.  Valid passwords are 10 to 128 characters
        # long and contain at least two digits.  Passwords must match.

        # Too short
        self.user_data['password'] = 'Pa33word4'
        self.user_data['password2'] = 'Pa33word4'
        self.assertFalse(TcsUserCreationForm(self.user_data).is_valid())

        # Less than two digits
        self.user_data['password'] = 'Pa3swordss'
        self.user_data['password2'] = 'Pa3swordss'
        self.assertFalse(TcsUserCreationForm(self.user_data).is_valid())

        # Too long
        self.user_data['password'] = '3' * 129
        self.user_data['password2'] = '3' * 129
        self.assertFalse(TcsUserCreationForm(self.user_data).is_valid())

        # Spaces should be allowed
        self.user_data['password'] = ' Pa3 s wor4 '
        self.user_data['password2'] = ' Pa3 s wor4 '
        self.assertTrue(TcsUserCreationForm(self.user_data).is_valid())

        # Passwords don't match
        self.user_data['password'] = 'Pa33word44'
        self.user_data['password2'] = 'Pa33word55'
        self.assertFalse(TcsUserCreationForm(self.user_data).is_valid())

        # Reset for next test
        self.user_data['password'] = 'Pa33word44'
        self.user_data['password2'] = 'Pa33word44'

        # An e-mail address is not valid if its normailized form is already in the
        # batabase.  Note that the call to create_user() creates a user based on the
        # normalized e-mail address, test@tcs.com.  The subsequent call to is_valid
        # takes the unnormalized e-mail address, which should not be valid.
        TcsUser.objects.create_user(self.user_data['email'].lower(), self.user_data['password'])
        self.assertFalse(TcsUserCreationForm(self.user_data).is_valid())

class TcsUserProfileFormTests(TestCase):
    """Tests for tcsuser.forms.TcsUserProfileForm."""

    def setUp(self):
        setUserData(self)
        self.user = TcsUser.objects.create_user(self.user_data['email'], self.user_data['password'])
        Address.objects.create(     # Follows the normalization rules
            street='217 Tyne Rd',
            city='Louisville',
            state='KY',
            country='US',
            postal_code='40207'
        )
        profile_form_data = {
            'name': 'Circus McGuirkus',
            'phone_number': '123-456-7890',
            'gender': 'M',
        }
        self.profile_form = TcsUserProfileForm(profile_form_data)

        self.assertEqual(TcsUser.objects.count(), 1)
        self.assertEqual(TcsUserProfile.objects.count(), 0)
        self.assertEqual(Address.objects.count(), 1)
        self.assertTrue(self.profile_form.is_valid())

    def testDuplicateAddress(self):
        """
        Creating a new profile with an address that is already in the database should not
        duplicate the address.  Case should not matter for matching addresses.
        """
        address = {                     # Upper-cased duplicate of setup address
            'street': '217 TYNE ROAD',
            'city': 'LOUISVILLE',
            'state': 'KY',
            'country': 'US',
            'postal_code': '40207',
        }

        address_form = AddressForm(address)
        self.assertTrue(address_form.is_valid())

        self.profile_form.instance.address = address_form.get_or_create()
        self.profile_form.instance.user = self.user
        self.profile_form.save()
        
        self.assertEqual(TcsUserProfile.objects.count(), 1) # Should have incremented since setup
        self.assertEqual(Address.objects.count(), 1)        # Should not have incremented since setup

    def testNewAddress(self):
        """
        Creating a new profile with an address that is not already in the database should create
        a new address instance.
        """
        address = {
            'street': '219 Tyne Road',
            'city': 'Louisville',
            'state': 'KY',
            'country': 'US',
            'postal_code': '40207',
        }

        address_form = AddressForm(address)
        self.assertTrue(address_form.is_valid())

        self.profile_form.instance.address = address_form.get_or_create() # Saves new address
        self.profile_form.instance.user = self.user
        self.profile_form.save()

        # Both counts should have incremented since setup
        self.assertEqual(TcsUserProfile.objects.count(), 1)
        self.assertEqual(Address.objects.count(), 2)

        # Make sure the fields of the new address are correct
        new_address = Address.objects.last()
        self.assertEqual(new_address.street, '219 Tyne Rd')
        self.assertEqual(new_address.city, 'Louisville')
