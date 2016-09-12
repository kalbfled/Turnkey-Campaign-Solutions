"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.apps import AppConfig

class VoterConfig(AppConfig):
    name = 'voter'
    verbose_name = 'Voter'

    def ready(self):
        """Connect signals."""
        super(VoterConfig, self).ready()
        import voter.signals
