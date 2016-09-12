"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django import forms
from tcsuser.models import TcsUser, TcsUserProfile

class TcsUserCreationForm(forms.ModelForm):
    """
    Use this form to validate input for creating a new TcsUser.  A valid password
    is 10 to 128 characters long and contains at least two digits.
    """
    class Meta:
        model = TcsUser
        fields = ('email', 'password')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
    # Use the inherited "email" field as-is, but customize its validation
    password = forms.RegexField(label='Passphrase', regex=r'.*\d.*\d.*', min_length=10, max_length=128,
        help_text = '10 to 128 characters with at least two digits',
        widget = forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages = {'min_length': 'Passwords must be at least 10 characters long.'})
    # Create a duplicate password field that must match 'password' for the form to validate
    password2 = forms.RegexField(label="Retype your passphrase", regex=r'.*\d.*\d.*', min_length=10, max_length=128,
        widget = forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages = {'min_length': 'Passwords must be at least 10 characters long.'})

    def clean_email(self):
        """
        The normalized e-mailed address must be unique.  Using the default validator
        only checks that the e-mail address as submitted is not already present.

        https://docs.djangoproject.com/en/1.8/ref/forms/validation/
        """
        email = self.cleaned_data['email']
        at_index = email.find('@') + 1
        normalized_email = email[:at_index] + email[at_index:].lower()
        if TcsUser.objects.filter(email=normalized_email).exists():
            # The e-mail address is a duplicate
            raise forms.ValidationError('That e-mail is already registered.', code='duplicate_email')
        return email

    def clean(self):
        """password and password2 must match."""
        cleaned_data = super(TcsUserCreationForm, self).clean()
        if cleaned_data.get('password') != cleaned_data.get('password2'):
            self.add_error('password2', forms.ValidationError('Passphrases must match.'))
        return cleaned_data

    def save(self):
        """Overridden so the password gets hashed."""
        return TcsUser.objects.create_user(self.cleaned_data['email'], self.cleaned_data['password'])

class TcsUserProfileForm(forms.ModelForm):
    """Use this form to modify a TcsUserProfile instance."""
    class Meta:
        model = TcsUserProfile
        exclude = ('address',)
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        return self.cleaned_data['name'].strip().title()
        
    def clean_phone_number(self):
        return self.cleaned_data['phone_number'].strip()

class TermsOfServiceForm(forms.Form):
    """Use this form to require a prospective user to accept the terms of service."""
    accepts_tos = forms.BooleanField(label='Terms of Service', help_text='accept')
