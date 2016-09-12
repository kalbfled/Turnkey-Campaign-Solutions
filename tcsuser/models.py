"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

# https://docs.djangoproject.com/en/1.8/topics/auth/customizing/#auth-custom-user

from address.models import Address
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class TcsUserManager(BaseUserManager):
    def create_user(self, email, password):
        """
        Creates and saves a TcsUser with the given email and password.
        """
        if not email:
            raise ValueError("The e-mail parameter must be set.")
        if not password:
            raise ValueError("The password parameter must be set.")
        email = self.normalize_email(email) # Inherited method; lowercases domain
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """The framework requires this method to be defined."""
        raise NotImplementedError("There are no superusers.")

class TcsUser(AbstractBaseUser):
    """
    This is a custom user model for TCS services that uses registrants'
    e-mail address as the unique identifier.

    Inherited fields: 'password' and 'last_login'

    Inherited methods: __str__, get_username, natural_key, is_anonymous,
        is_authenticated, set_password, check_password,
        get_unusable_password, has_unusable_password
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []    # 'password' will always be prompted
    objects = TcsUserManager()

    email = models.EmailField('e-mail', max_length=254, unique=True)
    is_active = models.BooleanField('active?', default=False) # override
    date_joined = models.DateTimeField(auto_now_add=True)

    # The auth framework requires the next two methods.
    def get_full_name(self):
        return self.profile.name

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.get_full_name()

class TcsUserProfile(models.Model):
    """
    Every activated TcsUser instance has an associated profile instance.
    The view tcsuser.views.tcsuserRegister creates the profile instance.
    """
    class Meta:
        verbose_name = 'profile'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', editable=False)
    name = models.CharField('Your name', max_length=100, help_text='As displayed to campaigns')
    address = models.ForeignKey(Address)            # Only care about the current address (many-to-one)
    phone_number = models.CharField(max_length=15)  # TODO - Country specific validation
    gender = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female')))
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'Profile for ' + self.name
