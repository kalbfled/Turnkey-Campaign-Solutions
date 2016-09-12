"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from smtplib import SMTPRecipientsRefused
from socket import gaierror

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sendActivationLink(sender, created, instance, **kwargs):
    """
    E-mail an activation link to new registrant.  The e-mail sender is the setting
    DEFAULT_FROM_EMAIL.  The activation link is a remote procedure call to
    tcsuser.views.activateUser.
    """
    if created:
        signed_email = TimestampSigner().sign(instance.email)
        # Test server; for development only.  For production, use settings.ALLOWED_HOSTS.
        link = 'http://localhost:8000'
        link += reverse('tcsuser_activate', args=(signed_email,))
        try:
            send_mail('Activate your account', link, settings.DEFAULT_FROM_EMAIL, [instance.email])
        except SMTPRecipientsRefused:
            print "Failed to send activation link.  Invalid e-mail recipients."
        except gaierror:
            print "Failed to send activation link.  No network connection?"
