# -*- coding: utf-8 -*-
# SubDL API (https://subdl.com/api-doc), a free API key is required
import re
from urllib.parse import quote_plus

import requests

from .. import _
from ..seeker import BaseSubtitlesError, SubtitlesErrors
from ..user_agents import get_api_user_agent, get_random_ua
from ..utilities import languageTranslate, log, saveSubtitle, stripYear, wantedLanguages

SEARCH_URL = "https://api.subdl.com/api/v1/subtitles"
DOWNLOAD_URL = "https://dl.subdl.com"
API_TIMEOUT = 15
DOWNLOAD_TIMEOUT = 30

# our iso639-1 codes -> SubDL language codes
SUBDL_LANG_CODES = {"pt-br": "BR_PT"}

settings_provider = None


def _api_key():
    key = settings_provider.getSetting("Subdl_API_KEY").strip()
    if not key:
        raise BaseSubtitlesError(SubtitlesErrors.NO_CREDENTIALS_ERROR, _("SubDL requires an API key"))
    return key


def _get(url, api_key, **kwargs):
    """requests.get() whose errors never show the api key (it is part of the url)"""
    try:
        return requests.get(url, **kwargs)
    except requests.Timeout:
        raise BaseSubtitlesError(SubtitlesErrors.TIMEOUT_ERROR, _("SubDL: timeout")) from None
    except requests.RequestException as e:
        raise BaseSubtitlesError(SubtitlesErrors.UNKNOWN_ERROR, _("SubDL: %s") % str(e).replace(quote_plus(api_key), "***").replace(api_key, "***")) from None


def _lang_name(item):
    code = (item.get("language") or "").lower()
    if code == "br_pt":
        code = "pt-br"
    return languageTranslate(code, 2, 0) or (item.get("lang") or "").capitalize()


def _search(params):
    api_key = _api_key()
    params = dict(params, api_key=api_key, subs_per_page=30)
    response = _get(SEARCH_URL, api_key, params=params, headers={"User-Agent": get_api_user_agent()}, timeout=API_TIMEOUT)
    if response.status_code in (401, 403):
        raise BaseSubtitlesError(SubtitlesErrors.INVALID_CREDENTIALS_ERROR, _("SubDL API key rejected"))
    try:
        data = response.json()
    except ValueError:
        data = None
    if not isinstance(data, dict) or response.status_code >= 500:
        raise BaseSubtitlesError(SubtitlesErrors.UNKNOWN_ERROR, _("SubDL: unexpected answer (HTTP %d)") % response.status_code)
    if not data.get("status"):  # i.e. not found
        log(__name__, "search failed: %s" % (data.get("error") or data.get("message")))
        return []
    return data.get("subtitles") or []


def test_credentials():
    _search({"film_name": "The Matrix", "type": "movie", "languages": "EN"})
    return _("SubDL API key OK")


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):
    langs = [SUBDL_LANG_CODES.get(code, code.upper()) for code in wantedLanguages(lang1, lang2, lang3)]
    if not langs:  # no languages would search all of them
        return [], "", ""
    params = {"languages": ",".join(langs)}
    if tvshow:
        params.update({"film_name": tvshow, "type": "tv"})
        if season:
            params["season_number"] = int(season)
        if episode:
            params["episode_number"] = int(episode)
    else:
        params.update({"film_name": stripYear(title), "type": "movie"})
        if year:
            params["year"] = year
    log(__name__, "search params: %s" % params)

    subtitles_list = []
    for item in _search(params):
        if not item.get("url"):
            continue
        name = item.get("release_name") or item.get("name") or title
        if tvshow and item.get("full_season"):
            name = "[S%02d] %s" % (int(item.get("season") or 0), name)
        subtitles_list.append({
            "id": item["url"],
            "filename": name,
            "language_name": _lang_name(item),
            "sync": False,
        })
    return subtitles_list, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    subtitle = subtitles_list[pos]
    url = DOWNLOAD_URL + subtitle["id"]
    api_key = _api_key()
    # the cdn serves free keys only for some url forms, try them in order
    attempts = [url, re.sub(r"\.(zip|rar)$", "", url), "%s?api_key=%s" % (url, quote_plus(api_key))]
    headers = {"User-Agent": get_random_ua(), "Accept": "*/*"}
    content = None
    for attempt in attempts:
        try:
            response = _get(attempt, api_key, headers=headers, timeout=DOWNLOAD_TIMEOUT)
        except BaseSubtitlesError as e:
            if e.code == SubtitlesErrors.TIMEOUT_ERROR:
                raise
            log(__name__, "download failed: %s" % e)
            continue
        if response.status_code == 200 and response.content:
            content = response.content
            break
        log(__name__, "download %s: HTTP %s" % (attempt.split("?")[0], response.status_code))
    if content is None:
        raise BaseSubtitlesError(SubtitlesErrors.UNKNOWN_ERROR, _("SubDL download failed"))
    filepath = saveSubtitle(tmp_sub_dir, subtitle["id"].rsplit("/", 1)[-1] or "subdl.zip", content)
    return False, subtitle["language_name"], filepath
