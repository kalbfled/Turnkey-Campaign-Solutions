"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-09 18:51
from __future__ import unicode_literals

from django.db import migrations, models
import django_countries.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street', models.CharField(max_length=50)),
                ('city', models.CharField(max_length=30)),
                ('state', models.CharField(help_text=b'2 letters', max_length=2, verbose_name=b'State, province, or territory')),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('postal_code', models.CharField(max_length=10)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]