# -*- coding: utf-8 -*-
# Wyzie Subs API (https://docs.wyzie.io/subs/usage/direct), a free key from https://store.wyzie.io/redeem is required
import re

import requests

from ..seeker import BaseSubtitlesError, SubtitlesErrors
from ..user_agents import get_api_user_agent
from ..utilities import downloadRating, imdbLookup, languageTranslate, log, saveSubtitle, wantedLanguages

API_URL = "https://sub.wyzie.io"
API_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 30

settings_provider = None


def _get(url, params=None, timeout=API_TIMEOUT):
    """requests.get() with the key, errors never show it (it is part of the url)"""
    key = settings_provider.getSetting("Wyzie_API_KEY").strip()
    if not key:
        raise BaseSubtitlesError(SubtitlesErrors.NO_CREDENTIALS_ERROR, "Wyzie requires an API key")
    try:
        response = requests.get(url, params=dict(params or {}, key=key), headers={"User-Agent": get_api_user_agent()}, timeout=timeout)
    except requests.Timeout:
        raise BaseSubtitlesError(SubtitlesErrors.TIMEOUT_ERROR, "Wyzie: timeout") from None
    except requests.RequestException as e:
        raise BaseSubtitlesError(SubtitlesErrors.UNKNOWN_ERROR, "Wyzie: %s" % str(e).replace(key, "***")) from None
    if response.status_code in (401, 403):
        raise BaseSubtitlesError(SubtitlesErrors.INVALID_CREDENTIALS_ERROR, "Wyzie API key rejected")
    return response


def _check(response):
    if response.status_code >= 400:  # raise_for_status() would show the url with the key
        raise BaseSubtitlesError(SubtitlesErrors.UNKNOWN_ERROR, "Wyzie: HTTP %d" % response.status_code)


def test_credentials():
    response = _get(API_URL + "/search", {"id": "tt0133093", "language": "en"})
    if response.status_code == 429:
        return "Wyzie API key OK, but the daily request limit is reached"
    _check(response)
    return "Wyzie API key OK"


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):
    langs = sorted(set("pt" if code == "pt-br" else code for code in wantedLanguages(lang1, lang2, lang3)))
    imdb_id = langs and imdbLookup(tvshow or title, None if tvshow else year, bool(tvshow))
    if not imdb_id:
        return [], "", ""
    params = {"id": imdb_id, "language": ",".join(langs), "format": "srt,sub"}
    if tvshow and season and episode:
        params.update({"season": int(season), "episode": int(episode)})
    log(__name__, "search params: %s" % params)
    response = _get(API_URL + "/search", params)
    if response.status_code == 400:  # "No subtitles found"
        return [], "", ""
    _check(response)

    subtitles_list = []
    for item in response.json():
        if not item.get("url"):
            continue
        code = item.get("language") or ""
        if code == "pt" and re.search(r"brazil|/BR/", "%s %s" % (item.get("display"), item.get("flagUrl")), re.I):
            code = "pt-br"
        subtitles_list.append({
            "id": item["url"],
            "filename": item.get("release") or item.get("fileName") or item.get("media") or title,
            "language_name": languageTranslate(code, 2, 0) or item.get("display") or code,
            "sync": False,
            "format": item.get("format") or "srt",
            "rating": downloadRating(item.get("downloadCount"), 500),
        })
    subtitles_list.sort(key=lambda s: -int(s["rating"]))
    return subtitles_list, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    subtitle = subtitles_list[pos]
    response = requests.get(subtitle["id"], headers={"User-Agent": get_api_user_agent()}, timeout=DOWNLOAD_TIMEOUT)
    response.raise_for_status()
    filepath = saveSubtitle(tmp_sub_dir, "%s.%s" % (subtitle["filename"], subtitle["format"]), response.content)
    return False, subtitle["language_name"], filepath
