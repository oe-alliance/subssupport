# -*- coding: utf-8 -*-
import functools
import os
import re
import struct
import unicodedata
from urllib.request import Request, urlopen

SUPRESS_LOG = True
IMDB_TIMEOUT = 10
# saveSubtitle(): extensions kept as they are, maximum file name length in bytes
SAVE_EXTENSIONS = ('.srt', '.sub', '.ass', '.ssa', '.vtt', '.txt', '.smi', '.mpl', '.zip', '.rar')
MAX_NAME_BYTES = 200


def log(module, msg):
    if SUPRESS_LOG:
        return
    print("%s %s" % (module, msg))


LANGUAGES = (

    # Full Language name[0]     podnapisi[1]  ISO 639-1[2]   ISO 639-1 Code[3]   Script Setting Language[4]   localized name id number[5]

    ("Albanian", "29", "sq", "alb", "0", 30201),
    ("Arabic", "12", "ar", "ara", "1", 30202),
    ("Armenian", "0", "hy", "arm", "2", 30203),
    ("Bosnian", "10", "bs", "bos", "3", 30204),
    ("Bulgarian", "33", "bg", "bul", "4", 30205),
    ("Catalan", "53", "ca", "cat", "5", 30206),
    ("Chinese", "17", "zh", "chi", "6", 30207),
    ("Croatian", "38", "hr", "hrv", "7", 30208),
    ("Czech", "7", "cs", "cze", "8", 30209),
    ("Danish", "24", "da", "dan", "9", 30210),
    ("Dutch", "23", "nl", "dut", "10", 30211),
    ("English", "2", "en", "eng", "11", 30212),
    ("Estonian", "20", "et", "est", "12", 30213),
    ("Persian", "52", "fa", "per", "13", 30247),
    ("Finnish", "31", "fi", "fin", "14", 30214),
    ("French", "8", "fr", "fre", "15", 30215),
    ("German", "5", "de", "ger", "16", 30216),
    ("Greek", "16", "el", "ell", "17", 30217),
    ("Hebrew", "22", "he", "heb", "18", 30218),
    ("Hindi", "42", "hi", "hin", "19", 30219),
    ("Hungarian", "15", "hu", "hun", "20", 30220),
    ("Icelandic", "6", "is", "ice", "21", 30221),
    ("Indonesian", "0", "id", "ind", "22", 30222),
    ("Italian", "9", "it", "ita", "23", 30224),
    ("Japanese", "11", "ja", "jpn", "24", 30225),
    ("Korean", "4", "ko", "kor", "25", 30226),
    ("Latvian", "21", "lv", "lav", "26", 30227),
    ("Lithuanian", "0", "lt", "lit", "27", 30228),
    ("Macedonian", "35", "mk", "mac", "28", 30229),
    ("Malay", "0", "ms", "may", "29", 30248),
    ("Norwegian", "3", "no", "nor", "30", 30230),
    ("Polish", "26", "pl", "pol", "31", 30232),
    ("Portuguese", "32", "pt", "por", "32", 30233),
    ("PortugueseBrazil", "48", "pb", "pob", "33", 30234),
    ("Romanian", "13", "ro", "rum", "34", 30235),
    ("Russian", "27", "ru", "rus", "35", 30236),
    ("Serbian", "36", "sr", "scc", "36", 30237),
    ("Slovak", "37", "sk", "slo", "37", 30238),
    ("Slovenian", "1", "sl", "slv", "38", 30239),
    ("Spanish", "28", "es", "spa", "39", 30240),
    ("Swedish", "25", "sv", "swe", "40", 30242),
    ("Thai", "0", "th", "tha", "41", 30243),
    ("Turkish", "30", "tr", "tur", "42", 30244),
    ("Ukrainian", "46", "uk", "ukr", "43", 30245),
    ("Vietnamese", "51", "vi", "vie", "44", 30246),
    ("Aymara", "0", "ay", "aym", "45", 30249),
    ("Esperanto", "0", "eo", "epo", "46", 30250),
    ("Galician", "0", "gl", "glg", "47", 30251),
    ("Georgian", "0", "ka", "geo", "48", 30252),
    ("Kazakh", "0", "kk", "kaz", "49", 30253),
    ("Luxembourgish", "0", "lb", "ltz", "50", 30254),
    ("Occitan", "0", "oc", "oci", "51", 30255),
    ("BosnianLatin", "10", "bs", "bos", "100", 30204),
    ("Farsi", "52", "fa", "per", "13", 30247),
   # ("English (US)"               , "2",        "en",            "eng",                 "100",                   30212  ),
   # ("English (UK)"               , "2",        "en",            "eng",                 "100",                   30212  ),
    ("Portuguese (Brazilian)", "48", "pt-br", "pob", "100", 30234),
    ("Portuguese (Brazil)", "48", "pb", "pob", "33", 30234),
    ("Portuguese-BR", "48", "pb", "pob", "33", 30234),
    ("Brazilian", "48", "pb", "pob", "33", 30234),
    ("Español (Latinoamérica)", "28", "es", "spa", "100", 30240),
    ("Español (España)", "28", "es", "spa", "100", 30240),
    ("Spanish (Latin America)", "28", "es", "spa", "100", 30240),
    ("Español", "28", "es", "spa", "100", 30240),
    ("SerbianLatin", "36", "sr", "scc", "100", 30237),
    ("Spanish (Spain)", "28", "es", "spa", "100", 30240),
    ("Chinese (Traditional)", "17", "zh", "chi", "100", 30207),
    ("Chinese (Simplified)", "17", "zh", "chi", "100", 30207))

REGEX_EXPRESSIONS = [r'[Ss]([0-9]+)[\]\[._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                      r'[\._ \-]([0-9]+)x([0-9]+)([^\\/]*)',  # foo.1x09
                      r'[\._ \-]([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',  # foo.109
                      r'([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',
                      r'[\\\\/\\._ -]([0-9]+)([0-9][0-9])[^\\/]*',
                      r'Season ([0-9]+) - Episode ([0-9]+)[^\\/]*',  # Season 01 - Episode 02
                      r'Season ([0-9]+) Episode ([0-9]+)[^\\/]*',  # Season 01 Episode 02
                      r'[\\\\/\\._ -][0]*([0-9]+)x[0]*([0-9]+)[^\\/]*',
                      r'[\[Ss]([0-9]+)\]_\[[Ee]([0-9]+)([^\\/]*)',  # foo_[s01]_[e01]
                      r'[\._ \-][Ss]([0-9]+)[\.\-]?[Ee]([0-9]+)([^\\/]*)',  # foo, s01e01, foo.s01.e01, foo.s01-e01
                      r's([0-9]+)ep([0-9]+)[^\\/]*',  # foo - s01ep03, foo - s1ep03
                      r'[Ss]([0-9]+)[\]\[ ._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                      r'[\\\\/\\._ \\[\\(-]([0-9]+)x([0-9]+)([^\\\\/]*)$'
                     ]

LANG_COUNTRY = {"ar": "AE",
                "ay": "BO",
                "bg": "BG",
                "bs": "BA",
                "ca": "AD",
                "cs": "CZ",
                "da": "DK",
                "de": "DE",
                "el": "GR",
                "en": "GB",
                "es": "ES",
                "et": "EE",
                "fa": "IR",
                "fi": "FI",
                "fr": "FR",
                "fy": "NL",
                "gl": "ES",
                "he": "IL",
                "hi": "IN",
                "hr": "HR",
                "hu": "HU",
                "hy": "AM",
                "id": "ID",
                "is": "IS",
                "it": "IT",
                "ja": "JP",
                "ka": "GE",
                "kk": "KZ",
                "ko": "KR",
                "ku": "IQ",
                "lb": "LU",
                "lt": "LT",
                "lv": "LV",
                "mk": "MK",
                "ms": "MY",
                "nl": "NL",
                "nb": "NO",
                "no": "NO",
                "oc": "FR",
                "pb": "BR",
                "pl": "PL",
                "pt": "PT",
                "pt-br": "BR",
                "ro": "RO",
                "ru": "RU",
                "sk": "SK",
                "sl": "SI",
                "sq": "AL",
                "sr": "RS",
                "sv": "SE",
                "th": "TH",
                "tr": "TR",
                "uk": "UA",
                "vi": "VN",
                "zh": "CN"}

# site language names (normalized) that languageTranslate() does not know
LANG_ALIASES = {
    'farsi persian': 'fa', 'brazilian portuguese': 'pt-br', 'brazillian portuguese': 'pt-br',
    'portuguese brazilian': 'pt-br', 'chinese bg code': 'zh', 'chinese simplified': 'zh',
    'chinese traditional': 'zh', 'big 5 code': 'zh', 'spanish spain': 'es', 'spanish latin america': 'es',
    'ukranian': 'uk'}

# Subscene season page names
SEASONS = ["Specials", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth",
           "Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth", "Seventeenth", "Eighteenth",
           "Nineteenth", "Twentieth", "Twenty-first", "Twenty-second", "Twenty-third", "Twenty-fourth", "Twenty-fifth"]

ROMAN = (('xx', 20), ('xix', 19), ('xviii', 18), ('xvii', 17), ('xvi', 16), ('xv', 15), ('xiv', 14), ('xiii', 13),
         ('xii', 12), ('xi', 11), ('x', 10), ('ix', 9), ('viii', 8), ('vii', 7), ('vi', 6), ('v', 5), ('iv', 4),
         ('iii', 3), ('ii', 2))
ROMAN_TO_INT = dict((r, str(n)) for r, n in ROMAN)
INT_TO_ROMAN = dict((str(n), r) for r, n in ROMAN)

LANGNAME_ISO6391 = dict(map(lambda lang: (lang[0], lang[2]), LANGUAGES))
LANGNAME_ISO6392 = dict(map(lambda lang: (lang[0], lang[3]), LANGUAGES))
# code -> name: the first row wins (Spanish, not Spanish (Spain))
ISO6391_LANGNAME = {}
ISO6392_LANGNAME = {}
for _lang in LANGUAGES:
    ISO6391_LANGNAME.setdefault(_lang[2], _lang[0])
    ISO6392_LANGNAME.setdefault(_lang[3], _lang[0])


def languageTranslate(lang, lang_from, lang_to):
    if lang_from == 0 and lang_to == 2:
        if lang in LANGNAME_ISO6391:
            return LANGNAME_ISO6391[lang]
    elif lang_from == 0 and lang_to == 3:
        if lang in LANGNAME_ISO6392:
            return LANGNAME_ISO6392[lang]
    if lang_from == 2 and lang_to == 0:
        if lang in ISO6391_LANGNAME:
            return ISO6391_LANGNAME[lang]
    elif lang_from == 3 and lang_to == 0:
        if lang in ISO6392_LANGNAME:
            return ISO6392_LANGNAME[lang]
    else:
        for x in LANGUAGES:
            if lang == x[lang_from]:
                return x[lang_to]


def allLang():
    return ["en",
            "fr",
            "hu",
            "cs",
            "pl",
            "sk",
            "pt",
            "pt-br",
            "es",
            "el",
            "ar",
            'sq',
            "hy",
            "ay",
            "bs",
            "bg",
            "ca",
            "zh",
            "hr",
            "da",
            "nl",
            "eo",
            "et",
            "fi",
            "gl",
            "ka",
            "de",
            "he",
            "hi",
            "is",
            "id",
            "it",
            "ja",
            "kk",
            "ko",
            "lv",
            "lt",
            "lb",
            "mk",
            "ms",
            "no",
            "oc",
            "fa",
            "ro",
            "ru",
            "sr",
            "sl",
            "sv",
            "th",
            "tr",
            "uk",
            "vi"]


def regex_movie(title):
    # from periscope
    movie_regexes = [r'(?P<movie>.*)[\.|\[|\(| ]{1}(?P<year>(?:(?:19|20)[0-9]{2}))(?P<teams>.*)']
    for regex in movie_regexes:
        match = re.search(regex, title, re.IGNORECASE)
        if match:
            return match.group('movie'), match.group('year')
    return '', ''


def regex_tvshow(compare, file, sub=""):
    tvshow = 0

    for regex in REGEX_EXPRESSIONS:
        response_file = re.findall(regex, file)
        if len(response_file) > 0:
            log(__name__, "Regex File Se: %s, Ep: %s," % (str(response_file[0][0]), str(response_file[0][1]),))
            tvshow = 1
            if not compare:
                title = re.split(regex, file)[0]
                for char in ['[', ']', '_', '(', ')', '.', '-']:
                    title = title.replace(char, ' ')
                if title.endswith(" "):
                    title = title[:-1]
                return title, response_file[0][0], response_file[0][1]
            else:
                break

    if (tvshow == 1):
        for regex in REGEX_EXPRESSIONS:
            response_sub = re.findall(regex, sub)
            if len(response_sub) > 0:
                try:
                    if (int(response_sub[0][1]) == int(response_file[0][1])):
                        return True
                except:
                    pass
        return False
    if compare:
        return True
    else:
        return "", "", ""


def hashFile(file_path):
    log(__name__, "Hash Standard file")
    filesize = os.path.getsize(file_path)
    if filesize < 65536 * 2:
        raise ValueError("file too small for hashing")
    with open(file_path, 'rb') as f:
        buffer = f.read(65536)
        f.seek(filesize - 65536, 0)
        buffer += f.read(65536)
    hash = filesize
    for (l_value,) in struct.iter_unpack('<q', buffer):
        hash = (hash + l_value) & 0xFFFFFFFFFFFFFFFF
    return filesize, "%016x" % hash


def stripYear(title):
    """'The Matrix (1999)' -> 'The Matrix'"""
    return re.sub(r"\s*\(\d{4}\)$", "", title or "").strip()


def yearMatch(found, year, tolerance=1):
    """True when a year is unknown or both differ by one at most (release years differ between countries)."""
    try:
        return abs(int(found) - int(year)) <= tolerance
    except (TypeError, ValueError):
        return True


def splitYear(text):
    """'The Matrix (1999)' or 'The Matrix 1999' -> ('The Matrix', '1999'), '1917' -> ('1917', None)"""
    text = (text or '').strip()
    m = re.match(r'(.+?)\s*(?:\((\d{4})\)|\s((?:19|20)\d{2}))$', text)
    return (m.group(1), m.group(2) or m.group(3)) if m else (text, None)


def releaseYearMatch(name, title, year):
    """True when a release name has no year besides the numbers of the title or one of them fits
    ('1917.2019', 'Blade.Runner.2049.2017'), resolutions like 1920x1080 are no years."""
    years = re.findall(r'(?<![\dx])(?:19|20)\d{2}(?![\dpx])', name, re.I)
    for number in re.findall(r'\d+', title or ''):
        if number in years:
            years.remove(number)
    return not years or any(yearMatch(y, year) for y in years)


def normalizeTitle(title):
    """'Fate of the Furious, The' -> 'the fate of the furious', 'Amélie' -> 'amelie'"""
    title = re.sub(r'^(.*), (the|a|an)$', r'\2 \1', (title or '').strip(), flags=re.I)
    title = unicodedata.normalize('NFKD', re.sub(r"['`]", '', title.lower()).replace('&', ' and '))
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in title if not unicodedata.combining(c))))


def matchTitle(title, year, results):
    """Value of the (name, year, value) result that fits title and year best, or None.

    Exact titles win over the main title before a colon ('Dune: Part One') and whole-word partial
    matches, then the same year and the closest length. Results more than one year off are skipped,
    partial matches need a year. One exact title two years off is taken when nothing matched the year.
    """
    wanted = normalizeTitle(title)
    if not wanted:
        return None
    partial_re = re.compile(r'\b%s\b' % re.escape(wanted))
    ranked, exact = [], []
    for name, found_year, value in results:
        name = name or ''
        found = normalizeTitle(name)
        if found == wanted:
            rank = 0
            exact.append((found_year, value))
        elif year and found_year and normalizeTitle(re.split(r':| - ', name)[0]) == wanted:
            rank = 1
        elif year and found_year and partial_re.search(found):
            rank = 2
        else:
            continue
        if yearMatch(found_year, year):
            same_year = not year or str(found_year) == str(year)
            ranked.append((rank, not same_year, abs(len(found) - len(wanted)), len(ranked), value))
    if ranked:
        return min(ranked)[-1]
    close = [value for found_year, value in exact if yearMatch(found_year, year, 2)]
    return close[0] if len(close) == 1 else None


def langCode(name):
    """Language name (ours or a site's) -> ISO 639-1 code ('pt-br' for Brazilian Portuguese) or None."""
    name = (name or '').strip()
    norm = re.sub(r'[^a-z0-9]+', ' ', name.lower()).strip()
    code = LANG_ALIASES.get(norm) or languageTranslate(name, 0, 2) or languageTranslate(norm.title(), 0, 2)
    return 'pt-br' if code == 'pb' else code


def wantedLanguages(*names):
    """{ISO 639-1 code: language name} of the requested languages known to the plugin, in request order."""
    wanted = {}
    for name in names:
        code = langCode(name)
        if code and code not in wanted:
            wanted[code] = name
    return wanted


def episodeFilters(season, episode):
    """Regexes for release names: (this episode, any episode, this season).

    S01E02, S01EP02, S01.Ep.2, S01E01E02 (multi episode), Season 1 Episode 2 and 1x02 are episodes,
    1920x1080 is not."""
    ep = r'e(?:p|pisode)?[ ._-]*'
    this_episode = re.compile(r'(?:s0*%d(?:[ ._-]*%s\d+)*?[ ._-]*%s0*%d|season[ ._-]*0*%d[ ._-]*%s0*%d|\b0*%dx0*%d)(?!\d)' % (
        season, ep, ep, episode, season, ep, episode, season, episode), re.I)
    any_episode = re.compile(r's\d+[ ._-]*%s\d+|\b\d{1,2}x\d{1,3}\b|\b%s\d+\b' % (ep, ep), re.I)
    this_season = r'(?<![a-z])s0*%d(?!\d)|season[ ._-]*0*%d(?!\d)' % (season, season)
    if 0 < season < len(SEASONS):  # no "Specials season"
        this_season += '|%s[ ._-]*season' % SEASONS[season].replace('-', '[ ._-]*')
    return this_episode, any_episode, re.compile(this_season, re.I)


def releaseKind(releases, filters):
    """'episode' when a release name is this episode, 'pack' for a whole season (no episode in
    the names), else None; filters from episodeFilters()."""
    this_episode, any_episode, this_season = filters
    if any(this_episode.search(r) for r in releases):
        return 'episode'
    if not any(any_episode.search(r) for r in releases) and any(this_season.search(r) for r in releases):
        return 'pack'
    return None


def romanVariations(words):
    """Word list with Roman numerals as digits and vice versa (['rocky', 'ii'] -> ['rocky', '2']),
    the first word is kept ('V for Vendetta', '5 Card Stud') and 'I' is left alone."""
    variations = [words]
    for table in (ROMAN_TO_INT, INT_TO_ROMAN):
        variant = words[:1] + [table.get(w, w) for w in words[1:]]
        if variant not in variations:
            variations.append(variant)
    return variations


def downloadRating(downloads, per_point=50):
    """Rating 1-10 (as string) from a download count."""
    return str(min(10, int(downloads or 0) // per_point + 1))


def createSession(referer=None):
    """requests session with a random browser user agent and an optional Referer."""
    import requests
    from .user_agents import get_random_ua
    session = requests.Session()
    session.headers['User-Agent'] = get_random_ua()
    if referer:
        session.headers['Referer'] = referer
    return session


def saveSubtitle(tmp_sub_dir, filename, content):
    """Writes a downloaded file to tmp_sub_dir and returns its path. The name is made safe and short
    enough for the file system, without a known extension it gets .zip/.rar/.ass/.vtt/.srt from the content."""
    from .seeker import SubtitlesDownloadError, SubtitlesErrors
    head = (content or b'')[:300].lstrip(b'\xef\xbb\xbf').lstrip()
    if not head or re.match(br'<(?:!doctype|html|\?xml|head|body|script|div)\b', head, re.I):
        raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, 'download returned no subtitle file')
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', '_', os.path.basename(filename or '')).strip(' .')
    root, ext = os.path.splitext(name)
    if ext.lower() not in SAVE_EXTENSIONS:
        root = name
        ext = '.zip' if content[:2] == b'PK' else '.rar' if content[:4] == b'Rar!' else \
            '.ass' if b'[script info]' in head.lower() else '.vtt' if head.startswith(b'WEBVTT') else '.srt'
    root = root.encode('utf-8')[:MAX_NAME_BYTES - len(ext.encode('utf-8'))].decode('utf-8', 'ignore').strip(' .')
    path = os.path.join(tmp_sub_dir, (root or 'subtitle') + ext)
    with open(path, 'wb') as f:
        f.write(content)
    return path


@functools.lru_cache(maxsize=32)
def _imdbSuggestions(query):
    """(title, year, id, kind) of the keyless IMDb suggestion API, cached per search process
    (several providers look up the same title), failures raise and are not cached."""
    import requests
    from urllib.parse import quote
    from .user_agents import get_random_ua
    url = "https://v3.sg.media-imdb.com/suggestion/x/%s.json" % quote(query.lower(), safe='')
    response = requests.get(url, headers={"User-Agent": get_random_ua()}, timeout=IMDB_TIMEOUT)
    response.raise_for_status()
    return tuple((i.get("l"), i.get("y"), i.get("id") or "", i.get("qid")) for i in response.json().get("d") or [])


def imdbLookup(title, year=None, tvshow=False):
    """Returns the IMDb id (tt...) of the title that matches title and year, or None."""
    query = stripYear(title)
    if not query:
        return None
    try:
        items = _imdbSuggestions(query)
    except Exception as e:
        log(__name__, "imdb lookup failed: %s" % e)
        return None
    kinds = ("tvSeries", "tvMiniSeries") if tvshow else ("movie", "tvMovie", "video")
    return matchTitle(query, year, [(name, found_year, imdb_id) for name, found_year, imdb_id, kind in items
                                    if imdb_id.startswith("tt") and kind in kinds])


def langToCountry(lang):
    if lang in LANG_COUNTRY:
        return LANG_COUNTRY[lang]
    return 'UNK'


class HeadRequest(Request):
    def get_method(self):
        return "HEAD"


def getFileSize(filepath):
    try:
        if os.path.isfile(filepath):
            return os.path.getsize(filepath)
    except Exception:
        return None
    if filepath.startswith('http://') or filepath.startswith('https://'):
        try:
            resp = urlopen(HeadRequest(filepath))
            return int(resp.info().get('Content-Length'))
        except Exception:
            return None
        finally:
            if 'resp' in locals():
                locals()['resp'].close()
    return None

# https://www.garykessler.net/library/file_sigs.html


def getCompressedFileType(filepath):
    signature_dict = {
                         b"\x50\x4b\x03\x04": "zip",
                         b"\x52\x61\x72\x21\x1A": "rar"
    }
    max_len = max(len(x) for x in signature_dict)
    with open(filepath, "rb") as f:
        file_start = f.read(max_len)
    for signature, filetype in signature_dict.items():
        if file_start.startswith(signature):
            return filetype
    return None


def detectSearchParams(title):
    print('[detectSearchParams] detecting parameters for - title: %s' % title)
    season = episode = tvshow = ""
    titlemovie, year = regex_movie(title)
    if titlemovie:
        title = titlemovie.strip()
    year = year.strip()
    # from xbmc-subtitles
    if year == "":                                            # If we have a year, assume no tv show
        if str(year) == "":                                          # Still no year: *could* be a tvshow
            title_tvshow, season, episode = regex_tvshow(False, title)
            if title_tvshow != "" and season != "" and episode != "":
                season = str(int(season)).strip()
                episode = str(int(episode)).strip()
                tvshow = title_tvshow.strip()
                title = ""
            else:
                season = ""                                              # Reset variables: could contain garbage from tvshow regex above
                episode = ""
                tvshow = ""
        else:
            year = ""
    print('[detectSearchParams] detected -  title: %s, year: %s, tvshow: %s, season: %s, episode: %s' % (title, year, tvshow, season, episode))
    return title, year, tvshow, season, episode


class SimpleLogger(object):

    LOG_FORMAT = "[{0}]{1}"
    LOG_NONE, LOG_ERROR, LOG_INFO, LOG_DEBUG = list(range(4))

    def __init__(self, prefix_name, log_level=LOG_INFO):
        self.prefix_name = prefix_name
        self.log_level = log_level

    def set_log_level(self, level):
        self.log_level = level

    def error(self, text, *args):
        if self.log_level >= self.LOG_ERROR:
            text = self._eval_message(text, *args)
            text = "[error] {0}".format(text)
            out = self._format_output(text)
            self._out_fnc(out)

    def info(self, text, *args):
        if self.log_level >= self.LOG_INFO:
            text = self._eval_message(text, *args)
            text = "[info] {0}".format(text)
            out = self._format_output(text)
            self._out_fnc(out)

    def debug(self, text, *args):
        if self.log_level == self.LOG_DEBUG:
            text = self._eval_message(text, *args)
            text = "[debug] {0}".format(text)
            out = self._format_output(text)
            self._out_fnc(out)

    def _eval_message(self, text, *args):
        return text % args if args else text

    def _format_output(self, text):
        return self.LOG_FORMAT.format(self.prefix_name, text)

    def _out_fnc(self, text):
        print(text)
