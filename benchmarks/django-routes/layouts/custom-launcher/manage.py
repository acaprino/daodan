#!/usr/bin/env python
import os
import sys


def launch(argv):
    from django.core.management import ManagementUtility

    ManagementUtility(argv).execute()


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")
    launch(sys.argv)
