# -*- coding:utf-8 -*-

__VERSION__ = '0.3.2'
import locale
locale.setlocale(locale.LC_ALL, '')

import gettext
import gtk
from gtk import glade

import os
from os.path import pardir, abspath, dirname, join

GETTEXT_DOMAIN = 'pyroom'
LOCALE_PATH = abspath(join(dirname(__file__), pardir, 'locales'))

# setup translation
languages_used = []
lc, encoding = locale.getdefaultlocale()
if lc:
    languages_used = [lc]
lang_in_env = os.environ.get('LANGUAGE', None)
if lang_in_env:
    languages_used.append(lang_in_env.split())

for module in gettext, glade:
    module.bindtextdomain(GETTEXT_DOMAIN, LOCALE_PATH)
    module.textdomain(GETTEXT_DOMAIN)

translation = gettext.translation(GETTEXT_DOMAIN, LOCALE_PATH,
                                  languages=languages_used,
                                  fallback=True)
import __builtin__
__builtin__._ = translation.gettext
