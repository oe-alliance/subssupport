# -*- coding: utf-8 -*-
# Finds subtitles in the configured search path and next to the played video file
import os
import re

from ..utilities import langCode, languageTranslate, log, releaseYearMatch, saveSubtitle, wantedLanguages

SUBTITLE_EXTENSIONS = (".srt", ".sub", ".ass", ".ssa")
MAX_DEPTH = 3
# tags between language and extension: movie.en.hi.srt, movie.en.forced.srt
TAGS = ("hi", "sdh", "cc", "forced", "default")

settings_provider = None


def _words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _code(tag):
    """'en', 'eng', 'pob', 'pt-br' -> ISO 639-1 code or None"""
    if re.match(r"^[a-z]{2,3}$|^pt-br$", tag):
        return langCode(languageTranslate(tag, 2 if len(tag) != 3 else 3, 0))
    return None


def _language(filename):
    """Language code in front of the extension, i.e. movie.en.srt / movie_ara.srt / movie.en.hi.srt"""
    tags = re.split(r"[._ -]+", os.path.splitext(filename)[0].lower())
    if tags[-2:] == ["pt", "br"]:
        tags[-2:] = ["pt-br"]
    while len(tags) > 2 and tags[-1] in TAGS and _code(tags[-2]):
        tags.pop()
    return _code(tags[-1]) if len(tags) > 1 else None


def _walk(path):
    base_depth = path.rstrip(os.sep).count(os.sep)
    for root, dirs, files in os.walk(path):
        if root.count(os.sep) - base_depth >= MAX_DEPTH:
            dirs[:] = []
        for name in files:
            if name.lower().endswith(SUBTITLE_EXTENSIONS):
                yield root, name


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):
    paths = []
    search_path = settings_provider.getSetting("LocalSearchPath").strip()
    if search_path and os.path.isdir(search_path):
        paths.append(search_path)
    if file_original_path and os.path.isfile(file_original_path):
        paths.append(os.path.dirname(file_original_path))
    title_words = _words(tvshow or title or "")
    if not title_words:
        return [], "", ""
    episode_tag = "s%02de%02d" % (int(season), int(episode)) if tvshow and season and episode else ""
    wanted = wantedLanguages(lang1, lang2, lang3)

    subtitles_list = []
    seen = set()
    for path in paths:
        for root, name in _walk(path):
            filepath = os.path.join(root, name)
            if filepath in seen:
                continue
            words = _words(name)
            joined = "".join(words)
            if not all(w in words for w in title_words) or (episode_tag and episode_tag not in joined):
                continue
            if not tvshow and not releaseYearMatch(name, title, year):
                continue
            code = _language(name)
            if code and wanted and code not in wanted:
                continue
            seen.add(filepath)
            subtitles_list.append({
                "filename": name,
                "path": filepath,
                "language_name": wanted.get(code) or languageTranslate(code, 2, 0) or next(iter(wanted.values()), "English"),
                "sync": False,
            })
    log(__name__, "found %d local subtitles in %s" % (len(subtitles_list), paths))
    return subtitles_list, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    subtitle = subtitles_list[pos]
    with open(subtitle["path"], "rb") as f:
        filepath = saveSubtitle(tmp_sub_dir, subtitle["filename"], f.read())
    return False, subtitle["language_name"], filepath
