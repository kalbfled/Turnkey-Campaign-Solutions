"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.models import Address
from django import forms
from localflavor.us.forms import USZipCodeField
from localflavor.us.us_states import US_STATES
import re

class AddressForm(forms.ModelForm):
    """Use this form to create and edit Address instances."""
    class Meta:
        model = Address
        exclude = ()
        widgets = {
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def checkPostalCode(self, code, country):
        """
        Test if 'code' is a valid postal code for the given country using the appropriate
        field from local-flavor.  If 'code' is not valid, the field's clean method will
        raise ValidationError.  This method exits with no return value if ValidationError
        is not raised and when the country doesn't have local-flavor data to use.
        """
        if country == 'US':
            USZipCodeField().clean(code)
#       elif:
            # TODO other countries for which localflavor submodules exist

    def checkState(self, state, country):
        """
        Return True if the two-letter state abbreviation is valid for the given country.
        Otherwise, return False.
        """
        if country == 'US':
            # US_STATES is tuple of tuples like (('KY', 'Kentucky'), ...)
            states = [s[0] for s in US_STATES]
#       elif:
            # TODO other countries for which localflavor submodules exist
        else:
            return True # No local flavor data to use            
        return state in states

    def clean_city(self):
        """Normalize the city by title-casing it."""
        return self.cleaned_data['city'].strip().title()

    def clean_postal_code(self):
        """Trim the postal code."""
        return self.cleaned_data['postal_code'].strip()

    def clean_state(self):
        """Normalize the state abbreviation by up-casing it."""
        return self.cleaned_data['state'].upper()

    def clean_street(self):
        """
        Normalize the street name by title-casing it and making common substitutions (i.e. Rd for Road).
        Also remove runs of spaces.
        """
        street = self.cleaned_data['street'].strip().title()
        street = re.sub(r'\bRoad\b', 'Rd', street)
        street = re.sub(r'\bStreet\b', 'Str', street)
        street = re.sub(r'\bAvenue\b', 'Ave', street)
        street = re.sub(r'\bParkway\b', 'Pkwy', street)
        street = re.sub(r'\bSuite\b', 'Ste', street)
        street = re.sub(r'\bApartment\b', 'Apt', street)
        street = re.sub(r'\s+', ' ', street) # Remove runs of spaces
        return street

    def clean(self):
        """
        Implement custom validation for the 'state' and 'postal_code' fields based on the selected country.
        """
        cleaned_data = super(AddressForm, self).clean()
        state = cleaned_data.get('state')
        country = cleaned_data.get('country')                    # A Country instance
        postal_code = cleaned_data.get('postal_code')

        # The state must be valid for the country
        if state and country and not self.checkState(state, country):
            self.add_error('state', forms.ValidationError('Invalid state for {0}.'.format(country)))

        # The postal code must be valid for the country
        if postal_code and country:
            try:
                self.checkPostalCode(postal_code, country)
            except forms.ValidationError as e:
                self.add_error('postal_code', e)
        return cleaned_data

    def get_or_create(self):
        """
        Call this method instead of AddressForm.save() when appropriate to avoid duplicating an address
        in the database.
        """
        if self.is_valid():
            address, created = Address.objects.get_or_create(
                street=self.cleaned_data['street'],
                city=self.cleaned_data['city'],
                state=self.cleaned_data['state'],
                country=self.cleaned_data['country'],
                postal_code=self.cleaned_data['postal_code'],
            )
            return address
        return None
