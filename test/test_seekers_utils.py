import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..', 'plugin'))

from seekers import utilities as u  # noqa: E402
from seekers.LocalDrive import service as localdrive  # noqa: E402
from seekers.seeker import SubtitlesDownloadError, isTimeout  # noqa: E402


class TestTitles(unittest.TestCase):

    def test_year_match(self):
        self.assertTrue(u.yearMatch('1999', '1999'))
        self.assertTrue(u.yearMatch(2000, '1999'))
        self.assertFalse(u.yearMatch('2001', '1999'))
        self.assertTrue(u.yearMatch(None, '1999'))
        self.assertTrue(u.yearMatch('1999', ''))
        self.assertTrue(u.yearMatch('2001', '1999', 2))

    def test_split_year(self):
        self.assertEqual(u.splitYear('The Matrix (1999)'), ('The Matrix', '1999'))
        self.assertEqual(u.splitYear('The Matrix 1999'), ('The Matrix', '1999'))
        self.assertEqual(u.splitYear('Blade Runner 2049 2017'), ('Blade Runner 2049', '2017'))
        self.assertEqual(u.splitYear('1917'), ('1917', None))
        self.assertEqual(u.splitYear(None), ('', None))

    def test_match_title(self):
        oldboy = [('Oldboy', '2013', 'remake'), ('Oldboy', '2003', 'original')]
        self.assertEqual(u.matchTitle('Oldboy', '2003', oldboy), 'original')
        self.assertEqual(u.matchTitle('Oldboy', '2013', oldboy), 'remake')
        self.assertIsNone(u.matchTitle('Oldboy', '2003', oldboy[:1]))  # ten years off
        self.assertEqual(u.matchTitle('Oldboy', '2005', oldboy[1:]), 'original')  # two years off, only one
        self.assertEqual(u.matchTitle('Oldboy', '2005', oldboy[1:] + [('Oldboy: Extras', '2020', 'x')]), 'original')  # partial off by years
        self.assertEqual(u.matchTitle('Oldboy', '2005', oldboy[1:] + [('Oldboy: Extras', '2005', 'x')]), 'x')  # year match wins
        dune = [('Dune', '1984', 'lynch'), ('Dune: Part One', '2021', 'villeneuve')]
        self.assertEqual(u.matchTitle('Dune', '2021', dune), 'villeneuve')
        self.assertEqual(u.matchTitle('Dune', '1984', dune), 'lynch')
        self.assertIsNone(u.matchTitle('Dune', '2021', dune[:1]))
        self.assertEqual(u.matchTitle('Dune', None, dune), 'lynch')
        self.assertIsNone(u.matchTitle('Kung Fu Panda 7', '2031', [('Kung Fu Panda', '2008', 1), ('Kung Fu Panda 4', '2024', 4)]))
        self.assertEqual(u.matchTitle('Fate of the Furious', '2017', [('Fate of the Furious, The', '2017', 8)]), 8)
        self.assertEqual(u.matchTitle('Amelie', '2001', [('Amélie', '2001', 'a')]), 'a')
        self.assertIsNone(u.matchTitle('', '2001', [('', '2001', 'a')]))

    def test_roman_variations(self):
        self.assertEqual(u.romanVariations(['rocky', 'ii']), [['rocky', 'ii'], ['rocky', '2']])
        self.assertEqual(u.romanVariations(['rocky', '2']), [['rocky', '2'], ['rocky', 'ii']])
        self.assertEqual(u.romanVariations(['v', 'for', 'vendetta']), [['v', 'for', 'vendetta']])
        self.assertEqual(u.romanVariations(['i', 'robot']), [['i', 'robot']])

    def test_release_year_match(self):
        self.assertTrue(u.releaseYearMatch('1917.2019.1080p.srt', '1917', '2019'))
        self.assertFalse(u.releaseYearMatch('1917.2019.1080p.srt', '1917', '2010'))
        self.assertTrue(u.releaseYearMatch('1917.srt', '1917', '2019'))
        self.assertTrue(u.releaseYearMatch('Blade.Runner.2049.2017.srt', 'Blade Runner 2049', '2017'))
        self.assertFalse(u.releaseYearMatch('Blade.Runner.1982.srt', 'Blade Runner', '2017'))
        self.assertTrue(u.releaseYearMatch('Movie.1920x1080.srt', 'Movie', '2017'))


class TestLanguages(unittest.TestCase):

    def test_lang_code(self):
        self.assertEqual(u.langCode('English'), 'en')
        self.assertEqual(u.langCode('Brazilian Portuguese'), 'pt-br')
        self.assertEqual(u.langCode('Portuguese (Brazilian)'), 'pt-br')
        self.assertEqual(u.langCode('PortugueseBrazil'), 'pt-br')
        self.assertEqual(u.langCode('Farsi/Persian'), 'fa')
        self.assertEqual(u.langCode('Spanish (Spain)'), 'es')
        self.assertIsNone(u.langCode('Klingon'))
        self.assertIsNone(u.langCode(None))

    def test_wanted_languages(self):
        self.assertEqual(u.wantedLanguages('English', None, 'Czech'), {'en': 'English', 'cs': 'Czech'})
        self.assertEqual(u.wantedLanguages('Serbian', 'SerbianLatin'), {'sr': 'Serbian'})
        self.assertEqual(u.wantedLanguages(None, 'Klingon'), {})

    def test_all_languages_roundtrip(self):
        for code in u.allLang():
            name = u.languageTranslate(code, 2, 0)
            self.assertTrue(name, code)
            self.assertEqual(u.langCode(name), code)
            self.assertEqual(u.wantedLanguages(name), {code: name})

    def test_canonical_names(self):
        for code, name in (('es', 'Spanish'), ('zh', 'Chinese'), ('sr', 'Serbian'), ('bs', 'Bosnian'),
                           ('fa', 'Persian'), ('pt-br', 'Portuguese (Brazilian)')):
            self.assertEqual(u.languageTranslate(code, 2, 0), name)
        self.assertEqual(u.languageTranslate('spa', 3, 0), 'Spanish')

    def test_flags(self):
        flags = os.path.join(test, '..', 'plugin', 'img', 'countries')
        for code in list(u.allLang()) + list(u.LANG_COUNTRY):
            country = u.langToCountry(code)
            self.assertTrue(os.path.isfile(os.path.join(flags, country + '.png')), '%s -> %s' % (code, country))


class TestEpisodes(unittest.TestCase):

    def test_episode_filters(self):
        this_episode, any_episode, this_season = u.episodeFilters(1, 2)
        for name in ('Show.S01E02.720p', 'Show S01EP02', 'Show.S01.Ep.2.HDTV', 'Show.S01E01E02', 'Show 1x02',
                     'Show Season 1 Episode 2'):
            self.assertTrue(this_episode.search(name), name)
        for name in ('Show.S01E12', 'Show.S01E01', 'Show.S11E02', 'Show 1x020', 'Show.S01E01E03'):
            self.assertFalse(this_episode.search(name), name)
        for name in ('Show.S01E05', 'Show 1x05', 'Show Ep.5', 'Show.S01EP05', 'Show Episode 5'):
            self.assertTrue(any_episode.search(name), name)
        for name in ('Show.S01.1920x1080.x264', 'Show Season 1 Complete', 'Show.1080p'):
            self.assertFalse(any_episode.search(name), name)
        for name in ('Show.S01.Complete', 'Show Season 1', 'Show - First Season', 'Show.First.Season'):
            self.assertTrue(this_season.search(name), name)
        self.assertFalse(this_season.search('Show.S11.Complete'))

    def test_specials(self):
        this_season = u.episodeFilters(0, 1)[2]
        self.assertFalse(this_season.search('Show - Specials Season'))
        self.assertTrue(this_season.search('Show.S00.Complete'))

    def test_ordinal_hyphen(self):
        this_season = u.episodeFilters(21, 1)[2]
        self.assertTrue(this_season.search('Show - Twenty-first Season'))
        self.assertTrue(this_season.search('Show.Twenty.First.Season'))

    def test_release_kind(self):
        filters = u.episodeFilters(10, 2)
        self.assertEqual(u.releaseKind(['Greys.Anatomy.S10E02.720p'], filters), 'episode')
        self.assertEqual(u.releaseKind(['Greys.Anatomy.S10.Complete', 'Greys.Anatomy.S10E02'], filters), 'episode')
        self.assertEqual(u.releaseKind(['Greys.Anatomy.Season.10.1080p'], filters), 'pack')
        self.assertIsNone(u.releaseKind(['Greys.Anatomy.S10E03'], filters))
        self.assertIsNone(u.releaseKind(['Greys.Anatomy.S09.Complete'], filters))
        self.assertIsNone(u.releaseKind(['Greys Anatomy - 2x02'], filters))


class TestSaveSubtitle(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, True)

    def save(self, name, content=b'1\n00:00:01,000 --> 00:00:02,000\nHi\n'):
        path = u.saveSubtitle(self.tmp, name, content)
        self.assertEqual(os.path.dirname(path), self.tmp)
        self.assertTrue(os.path.isfile(path))
        return os.path.basename(path)

    def test_extensions(self):
        self.assertEqual(self.save('movie.srt'), 'movie.srt')
        self.assertEqual(self.save('archive', b'PK\x03\x04rest'), 'archive.zip')
        self.assertEqual(self.save('archive', b'Rar!\x1a\x07\x00'), 'archive.rar')
        self.assertEqual(self.save('styled', b'\xef\xbb\xbf[Script Info]\nTitle: x\n'), 'styled.ass')
        self.assertEqual(self.save('web', b'WEBVTT\n\n00:01.000 --> 00:02.000\nHi\n'), 'web.vtt')
        self.assertEqual(self.save('Show.S01E01.720p.WEB'), 'Show.S01E01.720p.WEB.srt')

    def test_sanitise(self):
        self.assertEqual(self.save('a/b/../movie.srt'), 'movie.srt')
        self.assertEqual(self.save('Movie: Part 1? <x>.srt'), 'Movie_ Part 1_ _x_.srt')
        self.assertEqual(self.save('..'), 'subtitle.srt')
        self.assertEqual(self.save(''), 'subtitle.srt')
        self.assertEqual(self.save(None), 'subtitle.srt')
        long_name = self.save('é' * 300 + '.srt')
        self.assertTrue(long_name.endswith('.srt'))
        self.assertLessEqual(len(long_name.encode('utf-8')), u.MAX_NAME_BYTES)

    def test_html(self):
        for content in (b'', b'  \n', b'<!DOCTYPE html><html>', b'\xef\xbb\xbf\n <html>', b'<script>x</script>',
                        b'<div class="error">'):
            self.assertRaises(SubtitlesDownloadError, u.saveSubtitle, self.tmp, 'x.srt', content)
        self.assertEqual(os.listdir(self.tmp), [])


class TestImdbLookup(unittest.TestCase):

    def setUp(self):
        u._imdbSuggestions.cache_clear()

    def mocked(self, items):
        response = mock.Mock(status_code=200)
        response.json.return_value = {'d': items}
        return mock.patch('requests.get', return_value=response)

    def test_lookup(self):
        items = [{'l': 'Oldboy', 'y': 2013, 'id': 'tt1321511', 'qid': 'movie'},
                 {'l': 'Oldboy', 'y': 2003, 'id': 'tt0364569', 'qid': 'movie'},
                 {'l': 'Oldboy', 'y': 2003, 'id': 'tt9999999', 'qid': 'tvSeries'},
                 {'l': 'Oldboy Extras', 'id': 'nm0000001'}]
        with self.mocked(items) as get:
            self.assertEqual(u.imdbLookup('Oldboy', '2003'), 'tt0364569')
            self.assertEqual(u.imdbLookup('Oldboy (2013)', '2013'), 'tt1321511')
            self.assertEqual(u.imdbLookup('Oldboy', None, True), 'tt9999999')
            self.assertIsNone(u.imdbLookup('Oldboy', '1990'))
            self.assertEqual(get.call_count, 1)  # cached
            self.assertIn('/oldboy.json', get.call_args[0][0])

    def test_no_wrong_title(self):
        with self.mocked([{'l': 'Kung Fu Panda 4', 'y': 2024, 'id': 'tt21692408', 'qid': 'movie'}]):
            self.assertIsNone(u.imdbLookup('Kung Fu Panda 7', '2031'))

    def test_quote(self):
        with self.mocked([]) as get:
            u.imdbLookup('AC/DC: Live')
            self.assertIn('ac%2Fdc%3A%20live.json', get.call_args[0][0])

    def test_failure_not_cached(self):
        with mock.patch('requests.get', side_effect=OSError('down')):
            self.assertIsNone(u.imdbLookup('Dune', '2021'))
        with self.mocked([{'l': 'Dune', 'y': 2021, 'id': 'tt1160419', 'qid': 'movie'}]):
            self.assertEqual(u.imdbLookup('Dune', '2021'), 'tt1160419')


class TestTimeout(unittest.TestCase):

    def test_is_timeout(self):
        import socket
        self.assertTrue(isTimeout(socket.timeout()))
        self.assertFalse(isTimeout(ValueError('x')))
        try:
            import requests
            from urllib3.exceptions import MaxRetryError, ReadTimeoutError
        except ImportError:
            return
        reason = ReadTimeoutError(None, '/x', 'Read timed out.')
        self.assertTrue(isTimeout(requests.ConnectionError(MaxRetryError(None, '/x', reason))))
        self.assertFalse(isTimeout(requests.ConnectionError(MaxRetryError(None, '/x', OSError('refused')))))


class TestLocalDrive(unittest.TestCase):

    def test_language(self):
        self.assertEqual(localdrive._language('movie.en.srt'), 'en')
        self.assertEqual(localdrive._language('movie.en.hi.srt'), 'en')
        self.assertEqual(localdrive._language('movie.eng.forced.srt'), 'en')
        self.assertEqual(localdrive._language('movie.hi.srt'), 'hi')
        self.assertEqual(localdrive._language('movie.pob.srt'), 'pt-br')
        self.assertEqual(localdrive._language('movie.pt-br.srt'), 'pt-br')
        self.assertEqual(localdrive._language('movie_ara.srt'), 'ar')
        self.assertIsNone(localdrive._language('movie.srt'))
        self.assertIsNone(localdrive._language('en.srt'))

    def test_search(self):
        tmp = tempfile.mkdtemp()
        try:
            for name in ('1917.2019.1080p.en.srt', 'Blade.Runner.2049.2017.en.srt', 'Blade.Runner.1982.en.srt',
                         'movie.en.hi.srt', 'movie.pob.srt', 'movie.de.srt'):
                open(os.path.join(tmp, name), 'w').close()
            localdrive.settings_provider = mock.Mock(getSetting=lambda key: tmp)

            def search(title, year, *langs):
                langs = (list(langs) + [None] * 3)[:3]
                return sorted(s['filename'] for s in localdrive.search_subtitles('', title, '', year, 0, 0, False, False, *langs, None)[0])
            self.assertEqual(search('1917', '2019', 'English'), ['1917.2019.1080p.en.srt'])
            self.assertEqual(search('1917', '2010', 'English'), [])
            self.assertEqual(search('Blade Runner 2049', '2017', 'English'), ['Blade.Runner.2049.2017.en.srt'])
            self.assertEqual(search('movie', '', 'English'), ['movie.en.hi.srt'])
            self.assertEqual(search('movie', '', 'Portuguese (Brazilian)'), ['movie.pob.srt'])
            result = localdrive.search_subtitles('', 'movie', '', '', 0, 0, False, False, 'Portuguese (Brazilian)', None, None, None)[0]
            self.assertEqual(result[0]['language_name'], 'Portuguese (Brazilian)')
        finally:
            localdrive.settings_provider = None
            shutil.rmtree(tmp, True)


if __name__ == "__main__":
    unittest.main()
