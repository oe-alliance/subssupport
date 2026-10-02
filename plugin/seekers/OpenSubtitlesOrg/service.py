# -*- coding: utf-8 -*-
# OpenSubtitles.org legacy XML-RPC API (https://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC),
# login is optional (anonymous works). The API hands out real files to VIP members only, everybody else
# gets a "Become VIP member" stub, so those downloads come from the website (zip, limited per day/IP).
import gzip
import io
import os
import re
import time
import xmlrpc.client
import zipfile

import requests

from ..seeker import SubtitlesDownloadError, SubtitlesErrors
from ..user_agents import get_api_user_agent, get_random_ua
from ..utilities import downloadRating, hashFile, imdbLookup, languageTranslate, log, matchTitle, normalizeTitle, saveSubtitle, stripYear, \
    wantedLanguages, yearMatch

API_URL = "https://api.opensubtitles.org/xml-rpc"
WEB_URL = "https://www.opensubtitles.org/"
WEB_DOWNLOAD_URL = "https://dl.opensubtitles.org/en/download/sub/%s"
API_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 30
TOKEN_LIFETIME = 600  # tokens expire after 15 minutes without requests
VIP_STUB = b"osdb.link/vip"
SUB_EXTENSIONS = (".srt", ".sub", ".ssa", ".ass", ".smi", ".txt", ".vtt", ".mpl", ".tmp")

# our ISO 639-1 codes -> OpenSubtitles SubLanguageID where it is not column 3 of LANGUAGES
OS_LANG_IDS = {"pt-br": "pob", "es": "spa,spn,spl", "zh": "chi,zht,zhe"}
# OpenSubtitles ISO639 field -> our code
OS_ISO_CODES = {"pb": "pt-br", "zt": "zh", "ze": "zh", "sp": "es", "ea": "es", "me": "sr"}

settings_provider = None
_token = {}  # username -> (token, vip, time)


class _TimeoutTransport(xmlrpc.client.SafeTransport):
    user_agent = get_api_user_agent()

    def make_connection(self, host):
        connection = super().make_connection(host)
        connection.timeout = API_TIMEOUT
        return connection


def _call(method, *args):
    with xmlrpc.client.ServerProxy(API_URL, transport=_TimeoutTransport()) as server:
        return getattr(server, method)(*args)


def _check(result, what):
    status = (result or {}).get("status", "") if isinstance(result, dict) else ""
    if status.startswith("200"):
        return result
    if status.startswith("401"):
        raise SubtitlesDownloadError(SubtitlesErrors.INVALID_CREDENTIALS_ERROR, "OpenSubtitles.org login failed")
    if status.startswith("407"):
        raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "OpenSubtitles.org download limit reached, try again tomorrow")
    if status.startswith("429"):
        raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "OpenSubtitles.org: too many requests, try again later")
    raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "OpenSubtitles.org %s failed: %s" % (what, status or "no answer"))


def _credentials():
    username = settings_provider.getSetting("OpenSubtitlesOrg_username").strip() if settings_provider else ""
    password = settings_provider.getSetting("OpenSubtitlesOrg_password") if settings_provider else ""
    return (username, password) if username and password else ("", "")


def login(force=False):
    """Returns (token, vip), anonymous without username/password."""
    username, password = _credentials()
    cached = _token.get(username)
    if not force and cached and time.time() - cached[2] < TOKEN_LIFETIME:
        return cached[:2]
    result = _check(_call("LogIn", username, password, "en", get_api_user_agent()), "login")
    data = result.get("data") or {}
    vip = "vip" in str(data.get("UserRank", "")).lower() if isinstance(data, dict) else False
    _token[username] = (result["token"], vip, time.time())
    return result["token"], vip


def test_credentials():
    username = _credentials()[0]
    vip = login(force=True)[1]
    if not username:
        return "Anonymous login OK (no username/password set), downloads come from the website and are limited"
    return "Login OK (%s)" % ("VIP member" if vip else "no VIP, downloads come from the website and are limited")


def _lang_ids(codes):
    ids = []
    for code in codes:
        ids.extend((OS_LANG_IDS.get(code) or languageTranslate(code, 2, 3) or "").split(","))
    return ",".join(sorted(set(filter(None, ids))))


def _lang_name(item):
    code = (item.get("ISO639") or "").lower()
    code = OS_ISO_CODES.get(code, code)
    return languageTranslate(code, 2, 0) or item.get("LanguageName") or code


def _show_name(movie_name):
    """'"Breaking Bad" Pilot' -> 'Breaking Bad'"""
    match = re.match(r'\s*"([^"]+)"', movie_name or "")
    return match.group(1) if match else movie_name or ""


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):
    codes = wantedLanguages(lang1, lang2, lang3)
    language_ids = _lang_ids(codes)
    if not language_ids:
        return [], "", ""
    criteria = []
    if file_original_path and os.path.isfile(file_original_path):
        try:
            size, moviehash = hashFile(file_original_path)
            criteria.append({"moviehash": moviehash, "moviebytesize": str(size), "sublanguageid": language_ids})
        except Exception as e:
            log(__name__, "hash calculation failed: %s" % e)
    name = stripYear(tvshow or title)
    imdb_id = imdbLookup(name, None if tvshow else year, bool(tvshow))
    if imdb_id:
        criterion = {"imdbid": imdb_id[2:], "sublanguageid": language_ids}
    else:
        criterion = {"query": name, "sublanguageid": language_ids}
    if tvshow:
        criterion.update({"season": str(int(season or 0)), "episode": str(int(episode or 0))})
    criteria.append(criterion)
    log(__name__, "search criteria: %s" % criteria)
    token = login()[0]
    result = _call("SearchSubtitles", token, criteria)
    if str(result.get("status", "")).startswith(("401", "406")):  # expired token, no session
        token = login(force=True)[0]
        result = _call("SearchSubtitles", token, criteria)
    result = _check(result, "search")

    wanted_name = normalizeTitle(name)
    items = [item for item in result.get("data") or [] if isinstance(item, dict)]
    by_imdb = [item for item in items if item.get("MatchedBy") == "imdbid"]
    # the IMDb id was looked up by title, results of a different title mean it was the wrong one
    if by_imdb and not matchTitle(name, None if tvshow else year, [
            (_show_name(i.get("MovieName")) if tvshow else i.get("MovieName"), i.get("MovieYear"), True) for i in by_imdb]):
        log(__name__, "IMDb id %s is %s, not %s" % (imdb_id, by_imdb[0].get("MovieName"), name))
        items = [item for item in items if item.get("MatchedBy") != "imdbid"]
    subtitles_list, seen = [], set()
    for item in items:
        if item.get("IDSubtitleFile") in seen:
            continue
        matched_by = item.get("MatchedBy")
        if tvshow and matched_by != "moviehash":
            if (int(item.get("SeriesSeason") or 0), int(item.get("SeriesEpisode") or 0)) != (int(season or 0), int(episode or 0)):
                continue
            if matched_by == "fulltext" and normalizeTitle(_show_name(item.get("MovieName"))) != wanted_name:
                continue
        elif matched_by == "fulltext":  # query results contain sequels and other titles
            if normalizeTitle(item.get("MovieName")) != wanted_name or not yearMatch(item.get("MovieYear"), year):
                continue
        seen.add(item.get("IDSubtitleFile"))
        subtitles_list.append({
            "id": item.get("IDSubtitleFile"),
            "subtitle_id": item.get("IDSubtitle"),
            "link": item.get("SubDownloadLink"),
            "filename": item.get("SubFileName") or item.get("MovieReleaseName") or name,
            "language_name": _lang_name(item),
            "sync": matched_by == "moviehash",
            "rating": downloadRating(item.get("SubDownloadsCnt"), 200),
        })
    subtitles_list.sort(key=lambda s: (not s["sync"], -int(s["rating"])))
    return subtitles_list, "", ""


def _from_website(subtitle):
    """Zip from the website download link -> (file name, subtitle bytes)."""
    headers = {"User-Agent": get_random_ua(), "Referer": WEB_URL}
    response = requests.get(WEB_DOWNLOAD_URL % subtitle["subtitle_id"], headers=headers, timeout=DOWNLOAD_TIMEOUT)
    response.raise_for_status()
    if response.content[:2] != b"PK":  # html page with a captcha or the daily limit
        raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "OpenSubtitles.org website download limit reached (captcha), try again later or use a VIP account")
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(SUB_EXTENSIONS)]
        if not names:
            raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "OpenSubtitles.org archive contains no subtitle file")
        name = next((n for n in names if os.path.basename(n) == subtitle["filename"]), names[0])
        return os.path.basename(name), archive.read(name)


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    subtitle = subtitles_list[pos]
    filename, content = subtitle["filename"], b""
    if subtitle.get("link") and login()[1]:  # the API serves VIP members only, a gzipped srt
        response = requests.get(subtitle["link"], headers={"User-Agent": get_api_user_agent()}, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()
        try:
            content = gzip.decompress(response.content)
        except (OSError, EOFError):  # not gzipped, truncated
            content = response.content
        if VIP_STUB in content[:300]:
            log(__name__, "API returned the VIP stub, falling back to the website")
            content = b""
    if not content:
        filename, content = _from_website(subtitle)
    if VIP_STUB in content[:300]:
        raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "OpenSubtitles.org only delivers this subtitle to VIP members")
    return False, subtitle["language_name"], saveSubtitle(tmp_sub_dir, filename, content)
