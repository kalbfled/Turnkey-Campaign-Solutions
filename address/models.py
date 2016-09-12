"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.db import models
from django_countries.fields import CountryField

class Address(models.Model):
    """
    Voters, users, campaigns, etc. have addresses.  This model contains a timestamp to track changes
    of address rather than overwriting presumed old addresses.  This can help disambiguate voters.
    """
    street = models.CharField(max_length=50)        # Includes building number; i.e. 123 Main Street
    city = models.CharField(max_length=30)
    # TODO - Should this be required?  Do all countries have subdivisions?
    state = models.CharField('State, province, or territory', help_text='2 letters', max_length=2)
    country = CountryField()                        # https://pypi.python.org/pypi/django-countries
    postal_code = models.CharField(max_length=10)   # TODO - Verify that no country uses longer codes
    datetime = models.DateTimeField(auto_now_add=True)

    def getLocation(self):
        return '{0}, {1}'.format(self.city, self.state)

    def __unicode__(self):
        """Returns 'street address; City, State Country postal_code'"""
        return '{0}; {1}, {2} {3} {4}'.format(self.street, self.city, self.state, self.country.alpha3, self.postal_code)
