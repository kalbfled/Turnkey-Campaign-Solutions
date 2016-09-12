#!/usr/bin/env python

"""
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.
"""

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tcswebapp.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
