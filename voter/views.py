"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from voter.forms import VoterListForm
from voter.models import VoterList

@login_required
def voterLists(request):
    """
    If the user owns a campaign, display uploaded voter list files and a form
    for uploading a list file.  Otherwise, redirect to the home screen.
    
    The user can modify via a formset the 'is_active' value of uploaded lists.
    This view directly handles uploading new lists, but updates to previously
    uploaded lists target the view 'voterListsActivity'.
    """
    if not getattr(request.user, 'campaign', None):
        messages.error(request, "You don't own a campaign.")
        return HttpResponseRedirect(reverse('home'))
    # The user owns a campaign
    VoterListFormSet = modelformset_factory(VoterList, fields=('is_active',), extra=0)
    formset = VoterListFormSet(queryset=VoterList.objects.filter(campaign=request.user.campaign))
    if request.method == 'POST':
        upload_form = VoterListForm(request.POST, request.FILES)
        if upload_form.is_valid():  # Custom validation tests size and MIME type
            upload_form.instance.campaign = request.user.campaign
            upload_form.save()
            messages.success(request, 'Successfully uploaded a list of voters.')
    else:
        upload_form = VoterListForm()
    return render(request, 'voter/lists.html', {'upload_form': upload_form, 'formset': formset})

@login_required
@require_POST
def voterListsActivity(request):
    """Use this view to update the activity status of voter lists.  The user must own a campaign."""
    if not getattr(request.user, 'campaign', None):
        # TODO - test this
        messages.error(request, "You don't own a campaign.")
        return HttpResponseRedirect(reverse('home'))
    # The user owns a campaign
    VoterListFormSet = modelformset_factory(VoterList, fields=('is_active',), extra=0)
    formset = VoterListFormSet(request.POST)
    if formset.is_valid():
        # Make sure the user owns the campaign that owns the lists
        # TODO - test this with cURL
        for form in formset:
            if form.instance.campaign != request.user.campaign:
                messages.error(request, "You must manage the campaign that owns a voter list.")
                break
        else:
            # This gets executed if the for loop continues through exhaustion (all forms are valid)
            # https://docs.python.org/2/tutorial/controlflow.html#break-and-continue-statements-and-else-clauses-on-loops
            formset.save()
            messages.success(request, "You saved your voter list activity preferences.")
    return HttpResponseRedirect(reverse('voter_lists'))
