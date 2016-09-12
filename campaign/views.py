"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.forms import AddressForm
from campaign.forms import CampaignForm, CampaignSearchForm
from campaign.models import Campaign
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from tcsuser.models import TcsUser

@login_required
def campaignAdd(request, campaign_id, user_id):
    """Try to add a TcsUser instance to the workers of a Campaign instance."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    if campaign.owner != request.user:
        messages.error(request, "You do not own that campaign.")
    else:
        user = get_object_or_404(TcsUser, pk=user_id) # The volunteer to add
        if campaign.addWorker(user) is not None:
            messages.success(request, "You approved {0}.".format(user.get_full_name()))
        else:
            messages.error(request, "Could not approved {0}.".format(user.get_full_name()))
    return HttpResponseRedirect(reverse('campaign_manage', args=[campaign_id]))

@login_required
def campaignBlacklist(request, campaign_id, user_id):
    """Blacklist a TcsUser instance from a Campaign instance."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    if campaign.owner != request.user:
        messages.error(request, "You do not own that campaign.")
    else:
        user = get_object_or_404(TcsUser, pk=user_id) # The user to blacklist
        if campaign.addToBlacklist(user) is not None:
            messages.success(request, "You blacklisted {0}.".format(user.get_full_name()))
        else:
            messages.error(request, "Could not blacklist {0}.".format(user.get_full_name()))
    return HttpResponseRedirect(reverse('campaign_manage', args=[campaign_id]))

def campaignCreate(request):
    """Create a new Campaign instance if the user does not already own a campaign."""
    if request.method == 'POST':
        login_form = AuthenticationForm(request, data=request.POST)
        campaign_form = CampaignForm(request.POST)
        address_form = AddressForm(request.POST)
        if login_form.is_valid():
            # The credentials are valid, and the user is active.  AuthenticationForm.clean() calls
            # 'authenticate' and 'confirm_login_allowed'.  It saves the authenticated user as the
            # 'user_cache' attribute.
            if getattr(login_form.user_cache, 'campaign', None):
                messages.error(request, 'You may not create more than one campaign.')
                return HttpResponseRedirect(reverse('login'))
            if campaign_form.is_valid() and address_form.is_valid():
                campaign_form.instance.address = address_form.get_or_create()
                campaign_form.instance.owner = login_form.user_cache
                campaign_form.save()
                messages.success(request, 'You created a new campaign.')
                login(request, login_form.user_cache)
                return HttpResponseRedirect(reverse('home'))
    else:
        login_form = AuthenticationForm(request)
        campaign_form = CampaignForm()
        address_form = AddressForm()
    return render(request, 'campaign/create.html', {
        'login_form': login_form,
        'campaign_form': campaign_form,
        'address_form': address_form})

@login_required
def campaignEdit(request, campaign_id):
    """Edit a Campaign instance."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    if campaign.owner_id != request.user.pk:
        messages.error(request, "You cannot edit a campaign you do not own.")
        return HttpResponseRedirect(reverse('home'))
    if request.method == 'POST':
        address_form = AddressForm(request.POST, instance=campaign.address)
        campaign_form = CampaignForm(request.POST, instance=campaign)
        if address_form.is_valid() and campaign_form.is_valid():
            campaign_form.instance.address = address_form.get_or_create()
            campaign_form.save()
            messages.success(request, 'You updated "{0}."'.format(campaign.name))
            return HttpResponseRedirect(reverse('campaign_edit', args=[campaign_id]))
    else:
        address_form = AddressForm(instance=campaign.address)
        campaign_form = CampaignForm(instance=campaign)
    return render(request, 'campaign/edit.html', {
        'address_form': address_form,
        'campaign_form': campaign_form,
        'campaign': campaign})

@login_required
def campaignJoin(request, campaign_id):
    """Use this method when a user attempts to join a campaign."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    if campaign.addProspect(request.user) is not None:
        messages.success(request, 'You requested to join "{0}."'.format(campaign.name))
    else:
        messages.error(request, 'Cannot join "{0}."'.format(campaign.name))
    return HttpResponseRedirect(reverse('home'))

@login_required
def campaignLeave(request, campaign_id):
    """Use this method when a user attempts to leave a campaign."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    if campaign.removeWorker(request.user) is not None:
        messages.success(request, 'You left "{0}."'.format(campaign.name))
    else:
        messages.error(request, 'Cannot leave "{0}."'.format(campaign.name))
    return HttpResponseRedirect(reverse('home'))

@login_required
def campaignManage(request, campaign_id):
    """Allow the user to manage workers and prospective volunteers."""
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    if campaign.owner_id != request.user.pk:
        messages.error(request, "You cannot manage a campaign you do not own.")
        return HttpResponseRedirect(reverse('home'))
    # Tablulate the number of voters each worker has contacted
    volunteer_counts = [(volunteer, campaign.voterContactCount(volunteer)) for volunteer in campaign.workers.all()]
    # Sort volunteers by their count in descending order
    volunteer_counts.sort(key=lambda x: x[1], reverse=True)
    return render(request, 'campaign/manage.html', {
        'campaign': campaign,
        'volunteer_counts': volunteer_counts})

@login_required
def campaignSearch(request):
    """
    Find active campaigns based on a search query.  If the user supplies a value for 'id',
    ignore all other inputs.  Return at most 10 results.
    """
    if request.method == 'POST':
        form = CampaignSearchForm(request.POST)
        if form.is_valid():
            campaigns = Campaign.objects.filter(is_active=True)
            if form.cleaned_data['id']: # Must be None or a positive integer value
                campaigns = campaigns.filter(pk=form.cleaned_data['id']) # QuerySet; don't want a Campaign instance
            else:
                # Construct a query from the remaining non-blank form fields
                if form.cleaned_data['party'] != '':
                    campaigns = campaigns.filter(party=form.cleaned_data['party'])
                if form.cleaned_data['name'] != '':
                    campaigns = campaigns.filter(name__icontains=form.cleaned_data['name'])
                if form.cleaned_data['office'] is not None:
                    campaigns = campaigns.filter(office=form.cleaned_data['office'])
                if form.cleaned_data['district'] is not None:
                    campaigns = campaigns.filter(district=form.cleaned_data['district'])
    else:
        form = CampaignSearchForm()
        campaigns = []
    return render(request, 'campaign/search.html', {'form': form, 'campaigns': campaigns[:10]})
