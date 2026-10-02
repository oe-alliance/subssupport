# -*- coding: utf-8 -*-
# OpenSubtitles v3 addon of Stremio (https://opensubtitles-v3.strem.io/manifest.json), no key needed,
# needs the IMDb id, files are served as UTF-8 srt
import os

import requests

from ..user_agents import get_api_user_agent
from ..utilities import LANGUAGES, hashFile, imdbLookup, languageTranslate, log, saveSubtitle, wantedLanguages

API_URL = "https://opensubtitles-v3.strem.io/subtitles"
API_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 30

# 3-letter codes of the addon (OpenSubtitles ids, partly ISO 639-2/T) -> our ISO 639-1 codes
LANG_CODES = dict((lang[3], lang[2]) for lang in LANGUAGES if lang[4] != "100")
LANG_CODES.update({
    "pob": "pt-br", "zht": "zh", "zhe": "zh", "zho": "zh", "spn": "es", "spl": "es", "fra": "fr", "deu": "de",
    "ces": "cs", "nld": "nl", "ron": "ro", "gre": "el", "sqi": "sq", "hye": "hy", "mkd": "mk", "msa": "ms",
    "isl": "is", "fas": "fa", "slk": "sk", "srp": "sr", "kat": "ka"})

settings_provider = None


def _lang_name(code):
    return languageTranslate(code, 2, 0) or code


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):
    wanted = wantedLanguages(lang1, lang2, lang3)
    imdb_id = wanted and imdbLookup(tvshow or title, None if tvshow else year, bool(tvshow))
    if not imdb_id:
        return [], "", ""
    if tvshow:
        url = "%s/series/%s:%d:%d" % (API_URL, imdb_id, int(season or 0), int(episode or 0))
    else:
        url = "%s/movie/%s" % (API_URL, imdb_id)
    if file_original_path and os.path.isfile(file_original_path):
        try:
            size, moviehash = hashFile(file_original_path)
            url += "/videoHash=%s&videoSize=%d" % (moviehash, size)
        except Exception as e:
            log(__name__, "hash calculation failed: %s" % e)
    log(__name__, "search url: %s" % url)
    response = requests.get(url + ".json", headers={"User-Agent": get_api_user_agent()}, timeout=API_TIMEOUT)
    response.raise_for_status()

    subtitles_list = []
    for item in response.json().get("subtitles") or []:
        code = LANG_CODES.get(item.get("lang") or "")
        if not item.get("url") or code not in wanted:
            continue
        name = item.get("subtitleFileName") or item.get("movieReleaseName") or "%s.%s" % (tvshow or title, item.get("id"))
        subtitles_list.append({
            "id": item["url"],
            "filename": name,
            "language_name": _lang_name(code),
            "sync": item.get("m") == "h",  # matched by video hash
        })
    subtitles_list.sort(key=lambda s: not s["sync"])
    return subtitles_list, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    subtitle = subtitles_list[pos]
    response = requests.get(subtitle["id"], headers={"User-Agent": get_api_user_agent()}, timeout=DOWNLOAD_TIMEOUT)
    response.raise_for_status()
    return False, subtitle["language_name"], saveSubtitle(tmp_sub_dir, subtitle["filename"], response.content)
