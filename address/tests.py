"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.forms import AddressForm
from django.test import TestCase

class AddressFormTests(TestCase):
    """Tests for AddressForm."""

    def setUp(self):
        self.data = {
            'street': '  217  tyNe   road ',
            'city': '  louisVILLE ',
            'state': 'ky',
            'country': 'US',                # Field validation will not fix lowercase input
            'postal_code': ' 40207 ',
        }
        self.address_form = AddressForm(self.data)
        self.assertTrue(self.address_form.is_valid())
    
    def testCountryInterlock(self):
        """
        For countries for which local flavor data structures is available, ensure the state
        and postal code meet the given country's format.
        """
        
        # Invalid state for the United States
        self.data['state'] = 'zz'
        self.assertFalse(AddressForm(self.data).is_valid())

        # Invalid postal code for the United States
        self.data['state'] = 'KY'
        self.data['postal_code'] = '40-222-405'
        self.assertFalse(AddressForm(self.data).is_valid())

        # Any state and postal code input that meets the basic CharField restrictions should work
        # for countries without local flavor.
        self.data['country'] = 'CA'  # TODO - localflavor is available for Canada
        self.data['state'] = 'zz'
        self.assertTrue(AddressForm(self.data).is_valid())

    def testBasicNormalizations(self):
        """Test for expected cleaning of fields."""
        self.assertEqual(self.address_form.cleaned_data['city'], 'Louisville')
        self.assertEqual(self.address_form.cleaned_data['state'], 'KY')
        self.assertEqual(self.address_form.cleaned_data['postal_code'], '40207')
        
    def testStreetSubstitutions(self):
        """
        Verify the normalizing functionality of AddressForm.clean_street().
        """
        self.assertEqual(self.address_form.cleaned_data['street'], '217 Tyne Rd')
        # TODO - Test other abbreviations; maybe; if one works, they all will work
