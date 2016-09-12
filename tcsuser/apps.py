"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.apps import AppConfig

class TcsUserConfig(AppConfig):
    name = 'tcsuser'
    verbose_name = 'TcsUser'

    def ready(self):
        """Connect signals."""
        super(TcsUserConfig, self).ready()
        import tcsuser.signals
