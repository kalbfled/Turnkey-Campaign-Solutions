"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.


Django development settings for tcswebapp project.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# This is not the same as the production key.
SECRET_KEY = 'ke&-&a35#(kajvni488hf%da===2@@9c9pikf-=$bsn0g=$^#%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Application definition

INSTALLED_APPS = (
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'address',
    'campaign',
    'campaigner',
    'django_countries', # https://pypi.python.org/pypi/django-countries
    'tastypie',
    'tcsuser.apps.TcsUserConfig',
    'tcswebapp',
    'voter.apps.VoterConfig',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'tcswebapp.urls'

WSGI_APPLICATION = 'tcswebapp.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database - Use SQLite for development.
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tcs.sqlite',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = True
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'

# E-mail settings.  If these are not valid, the user will not be sent an activation link.
# They do not need to be set for unit testing to work as intended.
DEFAULT_FROM_EMAIL = ''    # TODO
EMAIL_HOST = ''            # TODO
EMAIL_PORT = 587
EMAIL_HOST_USER = ''       # TODO
EMAIL_HOST_PASSWORD = ''   # TODO
EMAIL_USE_TLS = True

# Custom user settings
AUTH_USER_MODEL = 'tcsuser.TcsUser'

# Tastypie settings
TASTYPIE_DEFAULT_FORMATS = ['json']

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/home/'

# This custom setting for the Voter application controls where uploaded voter lists are stored.
# This is a file path, not a URL, so don't include the leading '/'.
VOTER_LISTS_ROOT = 'voter_lists/'

# This is for convenient use of the Bootstrap "Danger" alert
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.ERROR: 'danger',
}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 86400  # 24 hours in seconds

COUNTRIES_FIRST = ['US']    # https://pypi.python.org/pypi/django-countries
