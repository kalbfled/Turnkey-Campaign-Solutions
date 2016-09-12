"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from campaign.models import Campaign
from datetime import date
from django import forms

class CampaignForm(forms.ModelForm):
    """Use this form to create and edit Campaign instances."""
    class Meta:
        model = Campaign
        exclude = ('owner', 'address')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'office': forms.Select(attrs={'class': 'form-control'}),
            'party': forms.Select(attrs={'class': 'form-control'}),
        }

    # Override election_date to specify the input format
    election_date = forms.DateField(input_formats=['%Y-%m-%d'], help_text='yyyy-mm-dd', required=False)

    def clean(self):
        """If is_electoral is true, the 'election_date' field is required."""
        cleaned_data = super(CampaignForm, self).clean()
        if cleaned_data.get('is_electoral') and cleaned_data.get('election_date') is None:
            self.add_error('election_date', forms.ValidationError('Required for electoral campaigns.'))
        return cleaned_data

    def clean_election_date(self):
        """A valid date cannot be in the past."""
        the_date = self.cleaned_data['election_date']
        if  the_date is not None and the_date < date.today():
            raise forms.ValidationError('Must be in the future.', code='past_election')
        return self.cleaned_data['election_date']

class CampaignSearchForm(forms.ModelForm):
    """Use this form to filter Campaign instances.  No field is required."""
    class Meta:
        model = Campaign
        fields = ('id', 'name', 'office', 'district', 'party')
        widgets = {
            'office': forms.Select(attrs={'class': 'form-control'}),
            'party': forms.Select(attrs={'class': 'form-control'}),
        }

    id = forms.IntegerField(min_value=1, required=False)
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
