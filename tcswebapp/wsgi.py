"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.


WSGI config for tcswebapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/

Also see
https://devcenter.heroku.com/articles/getting-started-with-django#django-settings
"""

import os

# Development settings only.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tcswebapp.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
