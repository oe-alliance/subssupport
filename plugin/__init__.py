# -*- coding: utf-8 -*-

from __future__ import absolute_import
__author__ = "mx3L"
__email__ = "mx3Lmail@gmail.com"
__copyright__ = 'Copyright (c) 2014-2023 mx3L, jbleyel'
__license__ = "GPL-v2"
__version__ = "1.5.9"

import gettext
from os.path import dirname, join

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE


def localeInit():
    gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
    gettext.textdomain("enigma2")
    gettext.bindtextdomain("SubsSupport", join(dirname(__file__), 'locale'))


def _(txt):
    t = gettext.dgettext("SubsSupport", txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)

from .subtitles import SubsSupport, SubsSupportStatus, initSubsSettings
