# -*- coding: UTF-8 -*-
#################################################################################
#
#    This module is part of SubsSupport plugin
#    Coded by mx3L (c) 2014
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#################################################################################

import difflib
import os
from re import match, search, split, sub
import shutil
import socket
import threading
import traceback
import zipfile

try:
    from .seekers import _, SubtitlesDownloadError, SubtitlesSearchError, \
        SubtitlesErrors, SubtitlesmoraSeeker, SubtitlecatSeeker, OpenSubtitles2Seeker, TitulkyComSeeker, \
        Subf2mSeeker, LocalDriveSeeker, IndexsubtitleSeeker, MoviesubtitlesSeeker, Sub_Scene_comSeeker, SubdlSeeker, \
        TitloviSeeker, PrijevodiOnlineSeeker, MySubsSeeker, SubsourceSeeker, YtssubsSeeker, JustsubtitlesSeeker, WyzieSeeker, \
        OpenSubtitlesOrgSeeker, StremioOSSeeker, GestdownSeeker
    from .seekers.seeker import BaseSeeker
    from .seekers.utilities import languageTranslate, langToCountry, \
        getCompressedFileType, detectSearchParams
    from .utils import SimpleLogger
except (ValueError, ImportError):  # searchsubs.py runs seek.py as a top-level module in its own process
    from seekers import _, SubtitlesDownloadError, SubtitlesSearchError, \
        SubtitlesErrors, SubtitlesmoraSeeker, SubtitlecatSeeker, OpenSubtitles2Seeker, TitulkyComSeeker, \
        Subf2mSeeker, LocalDriveSeeker, IndexsubtitleSeeker, MoviesubtitlesSeeker, Sub_Scene_comSeeker, SubdlSeeker, \
        TitloviSeeker, PrijevodiOnlineSeeker, MySubsSeeker, SubsourceSeeker, YtssubsSeeker, JustsubtitlesSeeker, WyzieSeeker, \
        OpenSubtitlesOrgSeeker, StremioOSSeeker, GestdownSeeker
    from seekers.seeker import BaseSeeker
    from seekers.utilities import languageTranslate, langToCountry, \
        getCompressedFileType, detectSearchParams
    from utils import SimpleLogger


SUBTITLES_SEEKERS = []
SUBTITLES_SEEKERS.append(LocalDriveSeeker)
SUBTITLES_SEEKERS.append(SubsourceSeeker)
SUBTITLES_SEEKERS.append(SubdlSeeker)
SUBTITLES_SEEKERS.append(OpenSubtitles2Seeker)
SUBTITLES_SEEKERS.append(WyzieSeeker)
SUBTITLES_SEEKERS.append(OpenSubtitlesOrgSeeker)
SUBTITLES_SEEKERS.append(StremioOSSeeker)
SUBTITLES_SEEKERS.append(GestdownSeeker)
SUBTITLES_SEEKERS.append(SubtitlesmoraSeeker)
SUBTITLES_SEEKERS.append(YtssubsSeeker)
SUBTITLES_SEEKERS.append(JustsubtitlesSeeker)
SUBTITLES_SEEKERS.append(IndexsubtitleSeeker)
SUBTITLES_SEEKERS.append(MoviesubtitlesSeeker)
SUBTITLES_SEEKERS.append(SubtitlecatSeeker)
SUBTITLES_SEEKERS.append(Sub_Scene_comSeeker)
SUBTITLES_SEEKERS.append(Subf2mSeeker)
SUBTITLES_SEEKERS.append(MySubsSeeker)
SUBTITLES_SEEKERS.append(TitulkyComSeeker)
SUBTITLES_SEEKERS.append(TitloviSeeker)
SUBTITLES_SEEKERS.append(PrijevodiOnlineSeeker)


class ErrorSeeker(BaseSeeker):
    def __init__(self, wseeker_cls, *args, **kwargs):
        self.id = wseeker_cls.id
        self.error = wseeker_cls.error
        self.provider_name = wseeker_cls.provider_name
        self.supported_langs = wseeker_cls.supported_langs
        self.description = getattr(wseeker_cls, 'description', "")
        self.tvshow_search = getattr(wseeker_cls, 'tvshow_search', True)
        self.movie_search = getattr(wseeker_cls, 'movie_search', True)
        self.default_settings = getattr(wseeker_cls, 'default_settings', dict())
        BaseSeeker.__init__(self, *args, **kwargs)

    def close(self):
        pass


# release name tokens, compared between the subtitle release and the played file
RANK_FEATURES = (
    # name, weight, {token: value}
    ('resolution', 8, {'2160p': '2160', '4k': '2160', 'uhd': '2160', '1080p': '1080', '1080i': '1080', '720p': '720', '576p': '576', '480p': '480'}),
    ('source', 15, {'web': 'web', 'webdl': 'web', 'webrip': 'web', 'amzn': 'web', 'nf': 'web', 'dsnp': 'web', 'hmax': 'web', 'atvp': 'web',
                    'bluray': 'bluray', 'bdrip': 'bluray', 'brrip': 'bluray', 'bdremux': 'bluray', 'remux': 'bluray', 'hddvd': 'bluray',
                    'hdtv': 'hdtv', 'pdtv': 'hdtv', 'dsr': 'hdtv', 'dvdrip': 'dvd', 'dvd': 'dvd', 'dvdscr': 'dvd', 'dvd5': 'dvd', 'dvd9': 'dvd',
                    'hdrip': 'hdrip', 'cam': 'cam', 'hdcam': 'cam', 'ts': 'cam', 'telesync': 'cam', 'hdts': 'cam'}),
    ('codec', 5, {'x264': '264', 'h264': '264', 'avc': '264', 'x265': '265', 'h265': '265', 'hevc': '265', 'xvid': 'xvid', 'divx': 'xvid', 'av1': 'av1'}),
    ('edition', 5, {'extended': 'extended', 'unrated': 'unrated', 'uncut': 'unrated', 'directors': 'directors', 'dc': 'directors',
                    'remastered': 'remastered', 'imax': 'imax', 'theatrical': 'theatrical', 'proper': 'proper', 'repack': 'proper'}),
)
RANK_NOGROUP = {'dl', 'rip', 'web', 'x264', 'x265', 'h264', 'h265', 'hevc', 'ac3', 'dts', 'aac', 'sub', 'subs', 'eng', 'srt', 'hi', 'sdh', 'forced', 'cc'}
# feature tokens which are words of titles too (DC League of Super-Pets, Uncut Gems, Charlotte's Web)
RANK_AMBIGUOUS = {'web', 'nf', 'amzn', 'dc', 'uncut', 'extended', 'unrated', 'directors', 'remastered', 'imax', 'theatrical', 'proper', 'repack',
                  'ts', 'cam', 'dvd', 'remux', 'dsr', 'avc', '4k', 'uhd'}
RANK_EPISODE = r'^s(\d{1,2})((?:e\d{1,3})+)$|^(\d{1,2})x(\d{2,3})$'  # S05E10, S05E10E11, 5x10
RANK_HARD = r'^(19|20)\d\d$|^s\d{1,2}(e\d{1,3})*$|^\d{1,2}x\d{2,3}$|^\d{3,4}[pi]$'  # year, episode, season, resolution


def releaseInfo(name):
    """name -> (tokens, features dict), features: group, episode, season, year and RANK_FEATURES"""
    name = name.replace('\\', '/').lower()
    # file path -> file name, "release1 / release2" stays one name
    name = os.path.basename(name) if name.startswith('/') or '://' in name else name.replace('/', ' ')
    root, ext = os.path.splitext(name)
    if ext[1:] in ('srt', 'sub', 'ass', 'ssa', 'vtt', 'txt', 'zip', 'rar', 'mkv', 'mp4', 'avi', 'ts', 'm2ts', 'mov', 'wmv', 'webm', 'mpg', 'mpeg', 'iso'):
        name = root
    name = sub(r'\[[^\]]*\]', ' ', name)  # [YTS.MX] tags
    name = sub(r'([hx])\.(26[45])', r'\1\2', name.replace('web-dl', 'webdl').replace("director's", 'directors'))
    tokens = [t for t in split(r'[^0-9a-z]+', name) if t]
    hard = [idx for idx, t in enumerate(tokens) if idx > 0 and match(RANK_HARD, t)]
    info = {'title': []}
    titleEnd = len(tokens)
    for idx, t in enumerate(tokens):
        episode = match(RANK_EPISODE, t)
        found = False
        if episode and episode.group(1):
            episodes = tuple(int(e) for e in split('e', episode.group(2))[1:])
            info.setdefault('episode', (int(episode.group(1)), episodes[0]))
            if len(episodes) > 1:
                info.setdefault('episodes', episodes)
            found = True
        elif episode:
            info.setdefault('episode', (int(episode.group(3)), int(episode.group(4))))
            found = True
        elif match(r'^s\d{1,2}$', t):
            if idx + 1 < len(tokens) and match(r'^e\d{1,3}$', tokens[idx + 1]):  # S02 E03
                info.setdefault('episode', (int(t[1:]), int(tokens[idx + 1][1:])))
            else:  # season pack
                info.setdefault('season', int(t[1:]))
            found = True
        elif t == 'season' and idx > 0 and idx + 1 < len(tokens) and tokens[idx + 1].isdigit():
            info.setdefault('season', int(tokens[idx + 1]))
            found = True
        elif match(r'^(19|20)\d\d$', t) and idx > 0:
            info['year'] = found = t
        for feature, _weight, values in RANK_FEATURES:
            # an ambiguous word in the title part is a feature only when nothing like a year follows
            if t in values and (idx > titleEnd or t not in RANK_AMBIGUOUS or idx > 0 and not [h for h in hard if h > idx]):
                info.setdefault(feature, values[t])
                found = True
        if found and titleEnd == len(tokens):
            titleEnd = idx
        if idx < titleEnd:
            info['title'].append(t)
    info['title'] = ' '.join(info['title'])
    # -GROUP, -GROUP.en, -GROUP-HI after the title and the release tokens
    group = search(r'-([0-9a-z]+)(?:[. _-][a-z]{2,7})*\s*$', name)
    group = group and group.group(1)
    if group and group not in RANK_NOGROUP and not match(RANK_HARD + r'|^e\d{1,3}$', group) and \
            not any(group in values for _feature, _weight, values in RANK_FEATURES) and group in tokens[titleEnd + 1:]:
        info['group'] = group
    return tokens, info


def rankRelease(release, reference):
    """Similarity of a subtitle release name to the played file name, 0-100"""
    if not release or not reference:
        return 0
    rtokens, rinfo = releaseInfo(release)
    vtokens, vinfo = releaseInfo(reference)
    # matching tokens: +weight, different: -weight, unknown: 0 -> 0..1
    points, total = 0, 0
    for feature, weight in [('group', 20), ('year', 7)] + [(f[0], f[1]) for f in RANK_FEATURES]:
        total += weight
        if feature in rinfo and feature in vinfo:
            points += weight if rinfo[feature] == vinfo[feature] else -weight
    score = 30 * difflib.SequenceMatcher(None, ' '.join(rtokens), ' '.join(vtokens)).ratio()
    score += 70 * (points + total) / (2.0 * total)
    # another title or episode never fits
    if rinfo['title'] and vinfo['title']:
        score *= 0.3 + 0.7 * difflib.SequenceMatcher(None, rinfo['title'], vinfo['title']).ratio()
    rseason = rinfo['episode'][0] if 'episode' in rinfo else rinfo.get('season')
    vseason = vinfo['episode'][0] if 'episode' in vinfo else vinfo.get('season')
    if 'episode' in rinfo and 'episode' in vinfo:
        repisodes = rinfo.get('episodes', rinfo['episode'][1:])
        vepisodes = vinfo.get('episodes', vinfo['episode'][1:])
        if rseason != vseason or not set(repisodes) & set(vepisodes):
            score = min(score, 10)
    elif rseason is not None and vseason is not None and rseason != vseason:
        score = min(score, 10)
    elif 'season' in rinfo and 'episode' in vinfo:  # season pack, the archive may not have this episode
        score -= 8
    if 'machine translated' in release.lower():  # Subtitlecat
        score -= 15
    return int(max(0, min(100, round(score))))


class SubsSeeker(object):
    SUBTILES_EXTENSIONS = ['.srt', '.sub', '.ass', '.ssa', '.vtt']

    def __init__(self, download_path, tmp_path, captcha_cb, delay_cb, message_cb, settings=None, settings_provider_cls=None, settings_provider_args=None, debug=False, providers=None):
        self.log = SimpleLogger(self.__class__.__name__, log_level=debug and SimpleLogger.LOG_DEBUG or SimpleLogger.LOG_INFO)
        self.download_path = download_path
        self.tmp_path = tmp_path
        self.seekers = []
        providers = providers or SUBTITLES_SEEKERS
        for seeker in providers:
            provider_id = seeker.id
            default_settings = seeker.default_settings
            default_settings['enabled'] = {'type': 'yesno', 'default': True, 'label': _('Enabled'), 'pos': -1}
            if settings_provider_cls is not None:
                settings = None
                settings_provider = settings_provider_cls(provider_id, default_settings, settings_provider_args)
                if hasattr(seeker, 'error') and seeker.error is not None:
                    settings_provider.setSetting('enabled', False)
                    self.seekers.append(ErrorSeeker(seeker, tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
                else:
                    self.seekers.append(seeker(tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
            elif settings is not None and provider_id in settings:
                settings_provider = None
                if hasattr(seeker, 'error') and seeker.error is not None:
                    self.seekers.append(ErrorSeeker(seeker, tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
                else:
                    self.seekers.append(seeker(tmp_path, download_path, settings[provider_id], settings_provider, captcha_cb, delay_cb, message_cb))
            else:
                settings = None
                settings_provider = None
                if hasattr(seeker, 'error') and seeker.error is not None:
                    self.seekers.append(ErrorSeeker(seeker, tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
                else:
                    self.seekers.append(seeker(tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))

    def getSubtitlesSimple(self, updateCB=None, title=None, filepath=None, langs=None):
        title, year, tvshow, season, episode = detectSearchParams(title or filepath)
        seekers = self.getProviders(langs)
        return self.getSubtitles(seekers, updateCB, title, filepath, langs, year, tvshow, season, episode)

    def getSubtitles(self, providers, updateCB=None, title=None, filepath=None, langs=None, year=None, tvshow=None, season=None, episode=None, timeout=10):
        self.log.info('getting subtitles list - title: %s, filepath: %s, year: %s, tvshow: %s, season: %s, episode: %s' % (
            title, filepath, year, tvshow, season, episode))
        subtitlesDict = {}
        threads = []
        prevTimeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        lock = threading.Lock()
        seekers = []
        for provider in providers:
            if isinstance(provider, str):
                seeker = self.getProvider(provider)
                if seeker is None:
                    self.log.error("unknown provider '%s', skipping...", provider)
                    continue
                provider = seeker
            if provider.error is not None:
                self.log.debug("provider '%s' has 'error' flag set, skipping...", provider)
            else:
                seekers.append(provider)
        if len(seekers) == 1:
            self._searchSubtitles(lock, subtitlesDict, updateCB, seekers[0], title, filepath, langs, season, episode, tvshow, year)
        else:
            for provider in seekers:
                threads.append(threading.Thread(target=self._searchSubtitles, args=(lock, subtitlesDict, updateCB, provider, title, filepath, langs, season, episode, tvshow, year)))
            for t in threads:
                t.daemon = True
                t.start()
            for t in threads:
                t.join()
        socket.setdefaulttimeout(prevTimeout)
        return subtitlesDict

    def getSubtitlesList(self, subtitles_dict, provider=None, langs=None, synced=False, nonsynced=False):
        subtitles_list = []
        if provider and provider in subtitles_dict:
            subtitles_list = subtitles_dict[provider]['list']
            for sub in subtitles_list:
                if 'provider' not in sub:
                    sub['provider'] = provider
                if 'country' not in sub:
                    sub['country'] = langToCountry(languageTranslate(sub['language_name'], 0, 2))
        else:
            for provider in subtitles_dict:
                provider_list = subtitles_dict[provider]['list']
                subtitles_list += provider_list
                for sub in provider_list:
                    if 'provider' not in sub:
                        sub['provider'] = provider
                    if 'country' not in sub:
                        sub['country'] = langToCountry(languageTranslate(sub['language_name'], 0, 2))
        if synced:
            subtitles_list = [x for x in subtitles_list if x['sync']]
        elif nonsynced:
            subtitles_list = [x for x in subtitles_list if not x['sync']]
        if langs:
            subtitles_list = [x for x in subtitles_list if languageTranslate(x['language_name'], 0, 2) in langs]
        return subtitles_list

    def rankSubtitlesList(self, subtitles_list, reference):
        """sets 'rank' (0-100) of every subtitle, similarity of its release name to reference"""
        for s in subtitles_list:
            s['rank'] = rankRelease(s.get('filename') or '', reference)
        return subtitles_list

    def getBestSubtitles(self, subtitles_list, langs, reference, min_rank=0):
        """candidates for an automatic download: hash/sync matches in language order,
        then the best ranked ones (>= min_rank) in language order"""
        langs = [lang for idx, lang in enumerate(langs) if lang and lang not in langs[:idx]]
        ranked = sorted(self.rankSubtitlesList(subtitles_list, reference), key=lambda x: x['rank'], reverse=True)
        langsOf = [(languageTranslate(s['language_name'], 0, 2), s) for s in ranked]
        synced = [s for lang in langs for slang, s in langsOf if slang == lang and s.get('sync')]
        best = [s for lang in langs for slang, s in langsOf if slang == lang and not s.get('sync') and s['rank'] >= min_rank]
        return synced + best

    def sortSubtitlesList(self, subtitles_list, langs=None, sort_langs=False, sort_rank=False, sort_sync=False, sort_provider=False, reference=None):
        def sortLangs(x):
            for idx, lang in enumerate(langs):
                if languageTranslate(x['language_name'], 0, 2) == lang:
                    return idx
            return len(langs)
        if langs and sort_langs:
            return sorted(subtitles_list, key=sortLangs)
        if sort_provider:
            return sorted(subtitles_list, key=lambda x: x['provider'])
        if sort_rank:
            # hash/sync matches first, then the best release name match
            if reference:
                self.rankSubtitlesList(subtitles_list, reference)
            return sorted(subtitles_list, key=lambda x: (bool(x.get('sync')), x.get('rank', 0)), reverse=True)
        if sort_sync:
            return sorted(subtitles_list, key=lambda x: x['sync'], reverse=True)
        return subtitles_list

    def downloadSubtitle(self, selected_subtitle, subtitles_dict, choosefile_cb, path=None, fname=None, overwrite_cb=None, settings=None):
        self.log.info('downloading subtitle "%s" with settings "%s"' % (selected_subtitle['filename'], settings or {}))
        if settings is None:
            settings = {}
        seeker = None
        for provider_id in subtitles_dict.keys():
            if selected_subtitle in subtitles_dict[provider_id]['list']:
                seeker = self.getProvider(provider_id)
                break
        if seeker is None:
            self.log.error('provider for "%s" subtitle was not found', selected_subtitle['filename'])
            raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "provider for the subtitle was not found")
        lang, filepath = seeker.download(subtitles_dict[provider_id], selected_subtitle)[1:3]
        if not filepath or not os.path.isfile(filepath):
            raise SubtitlesDownloadError(msg="download failed (invalid temp file path): %s" % filepath)
        compressed = getCompressedFileType(filepath)
        if compressed:
            subfiles = self._unpack_subtitles(filepath, self.tmp_path)
        else:
            subfiles = [filepath]
        if len(subfiles) == 0:
            self.log.error("no subtitles were downloaded!")
            raise SubtitlesDownloadError(msg="[error] no subtitles were downloaded")
        elif len(subfiles) == 1:
            self.log.debug('found one subtitle: "%s"', str(subfiles))
            subfile = subfiles[0]
        else:
            self.log.debug('found more subtitles: "%s"', str(subfiles))
            subfile = choosefile_cb(subfiles)
            if subfile is None:
                self.log.debug('no subtitles file choosed!')
                return
            self.log.debug('selected subtitle: "%s"', subfile)
        ext = os.path.splitext(subfile)[1].lower()
        if ext not in self.SUBTILES_EXTENSIONS:
            ext = os.path.splitext(selected_subtitle['filename'])[1].lower()
            if ext not in self.SUBTILES_EXTENSIONS:
                ext = '.srt'
        if fname is None:
            filename = os.path.basename(subfile)
            save_as = settings.get('save_as', 'default')
            if save_as == 'version':
                self.log.debug('filename creating by "version" setting')
                filename = selected_subtitle['filename']
                # Sanitize the filename to remove slashes and double dots
                filename = sub(r'[\\/]', '_', filename)  # Replace slashes with underscores
                filename = sub(r'\.\.', '.', filename)  # Replace double dots with a single dot
                if os.path.splitext(filename)[1].lower() not in self.SUBTILES_EXTENSIONS:
                    filename = os.path.splitext(filename)[0] + ext
            elif save_as == 'video':
                self.log.debug('filename creating by "video" setting')
                videopath = subtitles_dict[seeker.id].get('params', {}).get('filepath')
                if videopath:
                    filename = os.path.splitext(os.path.basename(videopath))[0] + ext
                else:
                    self.log.debug('no video path, keeping the subtitle file name')

            if settings.get('lang_to_filename', False):
                lang_iso639_1_2 = languageTranslate(lang, 0, 2)
                self.log.debug('appending language "%s" to filename', lang_iso639_1_2)
                filename, ext = os.path.splitext(filename)
                filename = "%s.%s%s" % (filename, lang_iso639_1_2, ext)
        else:
            self.log.debug('using provided filename')
            filename = fname + ext
        self.log.debug('filename: "%s"', filename)
        download_path = os.path.join(self.download_path, filename)
        if path is not None:
            self.log.debug('using custom download path: "%s"', path)
            download_path = os.path.join(path, filename)
        self.log.debug('download path: "%s"', download_path)

        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(download_path), exist_ok=True)

        if os.path.isfile(download_path) and overwrite_cb is not None:
            ret = overwrite_cb(download_path)
            if ret is None:
                self.log.debug('overwrite cancelled, returning temp path')
                return subfile
            elif not ret:
                self.log.debug('not overwriting, returning temp path')
                return subfile
            elif ret:
                self.log.debug('overwriting')
                try:
                    shutil.move(subfile, download_path)
                    return download_path
                except Exception as e:
                    self.log.error('moving "%s" to "%s" - %s', os.path.split(subfile)[-2:], os.path.split(download_path)[-2:], str(e))
                    return subfile
        try:
            shutil.move(subfile, download_path)
        except Exception as e:
            self.log.error('moving "%s" to "%s" - %s', os.path.split(subfile)[-2:], os.path.split(download_path)[-2:], str(e))
            return subfile
        return download_path

    def getProvider(self, provider_id):
        for s in self.seekers:
            if s.id == provider_id:
                return s

    def getProviders(self, langs=None, movie=True, tvshow=True):
        def check_langs(provider):
            for lang in provider.supported_langs:
                        if lang in langs:
                            return True
            return False

        providers = set()
        for provider in self.seekers:
            if provider.settings_provider.getSetting('enabled'):
                if langs:
                    if check_langs(provider):
                        if movie and provider.movie_search:
                            providers.add(provider)
                        if tvshow and provider.tvshow_search:
                            providers.add(provider)
                else:
                    if movie and provider.movie_search:
                        providers.add(provider)
                    if tvshow and provider.tvshow_search:
                        providers.add(provider)
        return list(providers)

    def _searchSubtitles(self, lock, subtitlesDict, updateCB, seeker, title, filepath, langs, season, episode, tvshow, year):
        try:
            subtitles = seeker.search(title, filepath, langs, season, episode, tvshow, year)
        except Exception as e:
            if isinstance(e, SubtitlesSearchError) and e.code != SubtitlesErrors.UNKNOWN_ERROR:
                self.log.info('%s: %s', seeker.id, e.msg)  # expected: missing key, bad login, timeout
            else:
                traceback.print_exc()
            with lock:
                subtitlesDict[seeker.id] = {'message': str(e), 'status': False, 'list': []}
                if updateCB is not None:
                    updateCB(seeker.id, False, str(e))  # sent as json
        else:
            with lock:
                subtitles['status'] = True
                subtitlesDict[seeker.id] = subtitles
                if updateCB is not None:
                    updateCB(seeker.id, True, subtitles)

    def _unpack_subtitles(self, filepath, dest_dir, max_recursion=3, used=None):
        if used is None:  # lower-case file names already taken in dest_dir
            used = set([os.path.basename(filepath).lower()])
        compressed = getCompressedFileType(filepath)
        if compressed == 'zip':
            self.log.debug('found "zip" archive, unpacking...')
            subfiles = self._unpack_zipsub(filepath, dest_dir, used)
        elif compressed == 'rar':
            self.log.debug('found "rar" archive, unpacking...')
            subfiles = self._unpack_rarsub(filepath, dest_dir, used)
        else:
            self.log.error('unsupported archive - %s', compressed)
            raise Exception("unsupported archive %s" % compressed)
        result = []
        error = None
        for s in subfiles:
            if os.path.splitext(s)[1].lower() in ('.rar', '.zip'):
                if max_recursion > 0:
                    try:
                        result.extend(self._unpack_subtitles(s, dest_dir, max_recursion - 1, used))
                    except Exception as e:  # corrupt archive, rarfile/unrar missing
                        self.log.error('cannot unpack "%s" - %s', os.path.basename(s), str(e))
                        error = e
            else:
                result.append(s)
        if error is not None and not result:
            raise error
        # natural sort, ep2 before ep10
        result.sort(key=lambda x: [int(t) if t.isdigit() else t.lower() for t in split(r'(\d+)', os.path.basename(x))])
        return result

    def _unpack_zipsub(self, zippath, destdir, used=None):
        with zipfile.ZipFile(zippath) as zf:
            return self._extract(zf, zippath, destdir, used)

    def _unpack_rarsub(self, rar_path, dest_dir, used=None):
        try:
            import rarfile
        except ImportError:
            self.log.error('rarfile lib not available -  pip install rarfile')
            raise
        with rarfile.RarFile(rar_path) as rf:
            return self._extract(rf, rar_path, dest_dir, used)

    def _extract(self, archive, archivePath, destdir, used=None, maxsize=10 * 1024 * 1024):
        used = set() if used is None else used
        subsfiles = []
        for subsfn in archive.namelist():
            ext = os.path.splitext(subsfn)[1].lower()
            if subsfn.endswith('/') or ext not in self.SUBTILES_EXTENSIONS + ['.rar', '.zip']:
                continue
            with archive.open(subsfn) as f:
                data = f.read(maxsize + 1)  # the header size can lie
            if len(data) > maxsize:
                self.log.error('skipping "%s", bigger than %dMB', subsfn, maxsize // (1024 * 1024))
                continue
            # flatten the path (episode folders) without overwriting other entries
            filename = subsfn.replace('\\', '/').strip('/').replace('/', '_')
            if filename.lower() in used:
                filename = "%s_%s" % (os.path.splitext(os.path.basename(archivePath))[0], filename)
            name, fext = os.path.splitext(filename)
            # file systems allow 255 bytes, keep room for the counter
            name = name.encode('utf-8')[:200 - len(fext.encode('utf-8'))].decode('utf-8', 'ignore')
            filename = name + fext
            count = 2
            while filename.lower() in used:
                filename = "%s_%d%s" % (name, count, fext)
                count += 1
            used.add(filename.lower())
            outpath = os.path.join(destdir, filename)
            with open(outpath, 'wb') as outfile:
                outfile.write(data)
            subsfiles.append(outpath)
        return subsfiles
