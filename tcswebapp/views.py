"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def home(request):
    """
    This is the main dashboard.  The template displays a list of campaigns the user supports,
    and this view queries to determine the number of voters the user has contacted on behalf of
    each campaign.
    """
    campaigns_supported = request.user.works_for.all()
    campaign_counts = [(campaign, campaign.voterContactCount(request.user)) for campaign in campaigns_supported]
    return render(request, 'tcswebapp/home.html', {'campaigns_supported': campaigns_supported, 'campaign_counts': campaign_counts})
