"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django import forms
from voter.models import Voter, VoterList

class VoterForm(forms.ModelForm):
    """Use this form to validate prospective Voter instances."""
    class Meta:
        model = Voter
        exclude = ('is_active', 'address')

    def clean_first_name(self):
        return self.cleaned_data['first_name'].strip().title()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].strip().title()

    def clean_gender(self):
        return self.cleaned_data['gender'].strip().upper()

    def clean_registrar_id(self):
        return self.cleaned_data['registrar_id'].strip()

    def clean_phone_number1(self):
        return self.cleaned_data['phone_number1'].strip()

    def clean_phone_number2(self):
        return self.cleaned_data['phone_number2'].strip()

    def clean_email(self):
        return self.cleaned_data['email'].strip()

class VoterListForm(forms.ModelForm):
    class Meta:
        model = VoterList
        exclude = ('is_active', 'processed')

    def clean_file_name(self):
        """The uploaded file must be less than 2MB, and it must be plain text, TSV, or CSV."""
        if self.cleaned_data['file_name'].size > 2000000:   # 2 megabytes
            raise forms.ValidationError('You may not exceed 2 megabytes per file.')
        if self.cleaned_data['file_name'].content_type not in ('text/plain', 'text/csv'):
            raise forms.ValidationError('Voter lists must be plain text, TSV, or CSV files.')
        return self.cleaned_data['file_name']
