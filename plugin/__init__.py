# -*- coding: utf-8 -*-
__author__ = "mx3L"
__email__ = "mx3Lmail@gmail.com"
__copyright__ = 'Copyright (c) 2014-2025 mx3L, jbleyel, popking159'
__license__ = "GPL-v2"
__mod__ = "MNASR"
__mod_email__ = "popking159@gmail.com"
__version__ = "1.7.0_r25"

from gettext import bindtextdomain, dgettext, gettext, textdomain
from os.path import dirname, join

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE


def localeInit():
    bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
    textdomain("enigma2")
    bindtextdomain("SubsSupport", join(dirname(__file__), 'locale'))


def _(txt):
    t = dgettext("SubsSupport", txt)
    if t == txt:
        t = gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)

from .subtitles import SubsSupport, SubsSupportStatus, initSubsSettings
