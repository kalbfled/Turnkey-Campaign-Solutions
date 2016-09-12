"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from address.forms import AddressForm
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from tcsuser.forms import TcsUserCreationForm, TcsUserProfileForm, TermsOfServiceForm
from tcsuser.models import TcsUserProfile

def tcsuserActivate(request, usercode):
    """
    This handles a remote procedure call for activating a TcsUser.  "usercode"
    is an e-mail address signed with a TimestampSigner.  If the signature is
    valid and less than or equal to 2 hours old, activate the TcsUser.
    """
    try:
        name = TimestampSigner().unsign(usercode, max_age=7200) # 2 hours
    except BadSignature:
        return HttpResponse("Invalid activation link.")
    except SignatureExpired:
        return HttpResponse("The activation link expired.")
    new_user = get_user_model().objects.get(email=name)
    new_user.is_active = True
    new_user.save()
    messages.success(request, "Thank you for activating your account.")
    return HttpResponseRedirect(reverse('login'))

@login_required
def tcsuserEdit(request):
    """Edit the logged-in user's profile."""
    if request.method == 'POST':
        profile_form = TcsUserProfileForm(request.POST, instance=request.user.profile)
        address_form = AddressForm(request.POST, instance=request.user.profile.address)
        if profile_form.is_valid() and address_form.is_valid():
            profile_form.instance.address = address_form.get_or_create()
            profile_form.save()
            messages.success(request, 'You updated your profile.')
            return HttpResponseRedirect(reverse('tcsuser_edit'))
    else:
        profile_form = TcsUserProfileForm(instance=request.user.profile)
        address_form = AddressForm(instance=request.user.profile.address)
    return render(request, 'tcsuser/edit.html', {'profile_form': profile_form, 'address_form': address_form})

def tcsuserRegister(request):
    """Create a new TcsUser instance and associated TcsUserProfile and Address instances."""
    if request.method == 'POST':
        user_form = TcsUserCreationForm(request.POST)
        profile_form = TcsUserProfileForm(request.POST)
        address_form = AddressForm(request.POST)
        tos_form = TermsOfServiceForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid() and address_form.is_valid() and tos_form.is_valid():
            profile_form.instance.address = address_form.get_or_create()
            profile_form.instance.user = user_form.save()
            profile_form.save()
            return HttpResponse('Thank you for registering.  Please check your e-mail within 2 hours for an activation link.')
        else:
            messages.error(request, 'Please fix the problems noted below.')
    else:
        user_form = TcsUserCreationForm()
        profile_form = TcsUserProfileForm()
        address_form = AddressForm()
        tos_form = TermsOfServiceForm()
    return render(request, 'tcsuser/register.html',
        {'user_form': user_form, 'profile_form': profile_form, 'address_form': address_form, 'tos_form': tos_form})
