"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.shortcuts import render

def campaignerCampaigns(request):
    return render(request, 'campaigner/campaigns.html')

def campaignerDial(request):
    return render(request, 'campaigner/dial.html')

def campaignerIR(request):
    """ir.html expects an "id" url parameter.  This is checked client side using JavaScript."""
    return render(request, 'campaigner/ir.html')
