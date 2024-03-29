#!/usr/bin/env python2.7
# coding: UTF-8

"""
A wrapper around %(prog)s that allows changing some options, such as which
site to operate on.
"""

import argparse
import locale
import os.path
import sys

from django.core.management import ManagementUtility

if hasattr(sys, 'setdefaultencoding'):
    sys.setdefaultencoding(locale.getpreferredencoding().lower())

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

PROG = os.path.basename(__file__)

parser = argparse.ArgumentParser(description=__doc__, epilog="""

  exec PYTHON_FILE [ARGS...]    Execute a python program in the Django
                                environment, à la ./manage.py shell
 
""", formatter_class=argparse.RawDescriptionHelpFormatter)
group = parser.add_mutually_exclusive_group()
group.add_argument('--dc', action='store_const', dest='site', const='dc')
group.add_argument('--d4t4', action='store_const', dest='site', const='d4t4')

group = parser.add_mutually_exclusive_group()
group.add_argument('--dev', action='store_const', dest='realm', const='dev')
group.add_argument('--prod', action='store_const', dest='realm', const='prod')
group.add_argument('--staging', action='store_const', dest='realm',
        const='staging')

parser.add_argument('--toolbar', action='store_true', dest='toolbar',
        help='Enable the Django debug toolbar.')

parser.add_argument('--db', action='store', dest='db',
        help='Specify the name of the database to use.')

parser.add_argument('--nodebug', action='store_true', dest='nodebug',
        help='Force DEBUG flag off.')

# http://stackoverflow.com/q/6488752/dont-parse-options-after-the-last-positional-argument
parser.add_argument('command', nargs=argparse.REMAINDER)

options = parser.parse_args()

# The original command is something like
#
# ./manage.py --toolbar runservers --other options
#
# The runservers command invokes manage.py again, and it has to pass on the
# arguments to the original manage.py command.
#
# ./manage.py --toolbar runservers --other --options
#                       \__________________________/
#                              options.command
# \________________________________________________/
#                    sys.argv

management_command_arguments = sys.argv[1:-len(options.command)]

if options.command[:1] == ['help']:
    parser.print_help()

if options.site is None:
    options.site = 'dc'

if options.realm is None:
    options.realm = 'dev'

django_settings_module = 'settings.%s_%s' % (options.site, options.realm)

os.environ['DJANGO_SETTINGS_MODULE'] = django_settings_module

# help(__import__) sayeth:
# “When importing a package, note that __import('A.B', ...) returns package A ‥”
__import__(django_settings_module)
settings = sys.modules[django_settings_module]

settings.MANAGEMENT_COMMAND_ARGUMENTS = management_command_arguments

if options.nodebug:
    settings.DEBUG = False

if options.db is not None:
    settings.DATABASES['default']['NAME'] = options.db

if options.toolbar:
    settings.enable_toolbar()

# configuration is now done

# this looks like a no-op, but django.conf.settings.configured() won’t be
# true until a setting value is requested
from django.conf import settings
settings.DEBUG

if options.command[0] == 'exec':
    sys.argv = options.command[1:]
    execfile(options.command[1])
else:
    utility = ManagementUtility([sys.argv[0]] + options.command)
    utility.execute()
