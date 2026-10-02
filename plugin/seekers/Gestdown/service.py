# -*- coding: utf-8 -*-
# Gestdown (https://www.gestdown.info), a free API in front of Addic7ed, TV episodes only, no key needed
import re
from urllib.parse import quote

import requests

from .. import _
from ..seeker import SubtitlesDownloadError, SubtitlesErrors
from ..user_agents import get_api_user_agent
from ..utilities import downloadRating, languageTranslate, log, normalizeTitle, saveSubtitle, stripYear, wantedLanguages, yearMatch

API_URL = "https://api.gestdown.info"
API_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 30

# our ISO 639-1 codes -> culture names Gestdown knows (Addic7ed has Spanish, Spanish (Spain) and Spanish (Latin America))
GESTDOWN_LANGS = {"es": ("es", "es-ES", "es-419")}

settings_provider = None


def _get(path, timeout=API_TIMEOUT):
    response = requests.get(API_URL + path, headers={"User-Agent": get_api_user_agent()}, timeout=timeout)
    if response.status_code == 429:
        raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, _("Gestdown: too many requests, try again in a minute"))
    return response


def _find_show(name, year):
    """Gestdown show id for a name ('Doctor Who' with year 2005 -> 'Doctor Who (2005)'), or None."""
    response = _get("/shows/search/%s" % quote(name))
    if response.status_code == 404:  # "Couldn't find show"
        return None
    response.raise_for_status()
    wanted = normalizeTitle(name)
    exact, variants = [], []
    for show in response.json().get("shows") or []:
        show_name = show.get("name") or ""
        if normalizeTitle(show_name) == wanted:
            exact.append(show)
            continue
        match = re.match(r'^(.*?)\s*\((\d{4}|[A-Z]{2})\)$', show_name)  # 'Doctor Who (2005)', 'The Office (US)'
        if match and normalizeTitle(match.group(1)) == wanted:
            found_year = match.group(2) if match.group(2).isdigit() else None
            if not year or not found_year or yearMatch(found_year, year):
                # same year first, then the US version, then the newest
                variants.append((not found_year or not year, match.group(2) != "US", -int(found_year or 0), show))
    if exact and not year:
        return exact[0]["id"]
    if variants:
        return min(variants, key=lambda v: v[:3])[3]["id"]
    return exact[0]["id"] if exact else None


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):
    if not tvshow or not season or not episode:
        return [], "", ""
    show_id = _find_show(stripYear(tvshow), year)
    if not show_id:
        return [], "", ""
    subtitles_list, seen = [], set()
    for code in wantedLanguages(lang1, lang2, lang3):
        for language in GESTDOWN_LANGS.get(code, (code,)):
            response = _get("/subtitles/get/%s/%d/%d/%s" % (show_id, int(season), int(episode), language))
            if response.status_code in (404, 423):  # unknown episode or language
                log(__name__, "no %s subtitles: %s" % (language, response.status_code))
                continue
            response.raise_for_status()
            for item in response.json().get("matchingSubtitles") or []:
                if not item.get("downloadUri") or item.get("subtitleId") in seen:
                    continue
                seen.add(item.get("subtitleId"))
                version = item.get("version") or "%s.S%02dE%02d" % (tvshow, int(season), int(episode))
                if item.get("hearingImpaired"):
                    version += " (HI)"
                if not item.get("completed", True):
                    version += " (incomplete)"
                subtitles_list.append({
                    "id": item["downloadUri"],
                    "filename": "%s S%02dE%02d %s" % (stripYear(tvshow), int(season), int(episode), version),
                    "language_name": languageTranslate(code, 2, 0) or item.get("language") or code,
                    "sync": False,
                    "rating": downloadRating(item.get("downloadCount"), 100),
                })
    subtitles_list.sort(key=lambda s: -int(s["rating"]))
    return subtitles_list, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    subtitle = subtitles_list[pos]
    response = _get(subtitle["id"], DOWNLOAD_TIMEOUT)
    response.raise_for_status()
    return False, subtitle["language_name"], saveSubtitle(tmp_sub_dir, subtitle["filename"] + ".srt", response.content)
