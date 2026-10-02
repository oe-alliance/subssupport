import os
import sys
import unittest
test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..', 'plugin'))
from seek import SubsSeeker, rankRelease, releaseInfo


def order(reference, releases):
    return sorted(releases, key=lambda r: rankRelease(r, reference), reverse=True)


class TestRank(unittest.TestCase):

    def test_release_info(self):
        info = releaseInfo('The.Batman.2022.1080p.WEB-DL.DDP5.1.Atmos.H.264-CMRG.mkv')[1]
        self.assertEqual(info, {'title': 'the batman', 'group': 'cmrg', 'year': '2022', 'resolution': '1080', 'source': 'web', 'codec': '264'})
        info = releaseInfo('Severance.S02E03.720p.WEB.h264-FLUX.en.srt')[1]
        self.assertEqual(info['episode'], (2, 3))
        self.assertEqual(info['group'], 'flux')
        self.assertEqual(releaseInfo('Show.1x05.HDTV.XviD')[1]['episode'], (1, 5))
        self.assertNotIn('group', releaseInfo('Movie.2020.1080p.WEB-DL')[1])
        self.assertEqual(releaseInfo('2012.2009.720p.BluRay')[1]['year'], '2009')  # title 2012 is no year
        self.assertEqual(releaseInfo('Breaking.Bad.S01.BluRay.x264-REWARD / FGT')[1]['title'], 'breaking bad')
        self.assertEqual(releaseInfo('/tmp/subs/Breaking.Bad.S01E02.srt')[1]['episode'], (1, 2))

    def test_movie_order(self):
        reference = 'The.Batman.2022.1080p.WEB-DL.DDP5.1.Atmos.H.264-CMRG.mkv'
        releases = ['The.Batman.2022.720p.HDCAM-C1NEM4',
                    'The.Batman.2022.2160p.BluRay.REMUX.HEVC-FGT',
                    'The Batman (2022)',
                    'The.Batman.2022.1080p.WEBRip.x264-RARBG',
                    'The.Batman.2022.1080p.WEB-DL.DDP5.1.Atmos.H.264-CMRG']
        ranked = order(reference, releases + ['Joker.2019.1080p.WEB-DL.H264-CMRG'])
        self.assertEqual(ranked[:3], [
            'The.Batman.2022.1080p.WEB-DL.DDP5.1.Atmos.H.264-CMRG',
            'The.Batman.2022.1080p.WEBRip.x264-RARBG',
            'The Batman (2022)'])
        self.assertGreaterEqual(rankRelease(releases[-1], reference), 90)
        self.assertLess(rankRelease('Joker.2019.1080p.WEB-DL.H264-CMRG', reference), 50)  # same group, other movie

    def test_episode_order(self):
        reference = '/media/hdd/movie/Severance.S02E03.1080p.ATVP.WEB-DL.DDP5.1.H.264-NTb.mkv'
        releases = ['Severance.S02E04.1080p.ATVP.WEB-DL.DDP5.1.H.264-NTb',
                    'Severance - 02x03 - Who Is Alive.WEB.FLUX.English',
                    'Severance.S02E03.720p.WEB.h264-FLUX',
                    'Severance.S02E03.1080p.ATVP.WEB-DL.DDP5.1.H.264-NTb.en.srt']
        ranked = order(reference, releases)
        self.assertEqual(ranked[0], 'Severance.S02E03.1080p.ATVP.WEB-DL.DDP5.1.H.264-NTb.en.srt')
        self.assertEqual(ranked[-1], 'Severance.S02E04.1080p.ATVP.WEB-DL.DDP5.1.H.264-NTb')
        self.assertLess(rankRelease(releases[0], reference), 60)

    def test_title_words(self):
        # feature words in titles: DC, Uncut, Web
        for name, title in [('DC.League.of.Super-Pets.2022.1080p.WEB-DL.H.264-EVO', 'dc league of super pets'),
                            ('Uncut.Gems.2019.1080p.WEBRip.x264-RARBG', 'uncut gems'),
                            ('Charlottes.Web.2006.1080p.BluRay.x264-HD4U', 'charlottes web')]:
            info = releaseInfo(name)[1]
            self.assertEqual(info['title'], title)
            self.assertNotIn('edition', info)
        self.assertEqual(releaseInfo('Charlottes.Web.2006.1080p.BluRay.x264-HD4U')[1]['source'], 'bluray')
        self.assertEqual(releaseInfo('Movie.TS.mkv')[1]['source'], 'cam')
        self.assertLess(rankRelease('Batman.Begins.2005.1080p.WEB-DL.H.264-EVO', 'DC.League.of.Super-Pets.2022.1080p.WEB-DL.DDP5.1.H.264-EVO.mkv'), 40)
        self.assertLess(rankRelease('Good.Time.2017.1080p.WEBRip.x264-RARBG', 'Uncut.Gems.2019.1080p.WEBRip.x264-RARBG.mp4'), 40)

    def test_group(self):
        self.assertNotIn('group', releaseInfo('X-Men')[1])
        self.assertEqual(releaseInfo('X-Men.2000.1080p.BluRay.x264-SPARKS')[1]['group'], 'sparks')
        self.assertNotIn('group', releaseInfo('Movie-2020-1080p')[1])
        self.assertNotIn('group', releaseInfo('Show.S01E01-E03')[1])
        self.assertEqual(releaseInfo('Movie.Name.2019.1080p.BluRay.x264-SPARKS-HI')[1]['group'], 'sparks')
        self.assertEqual(releaseInfo('Movie.Name.2019.1080p.BluRay.x264-SPARKS.forced.en')[1]['group'], 'sparks')

    def test_seasons(self):
        reference = 'Severance.S02E03.1080p.WEB.h264-ETHEL.mkv'
        self.assertEqual(releaseInfo('Severance.S01.1080p.WEB.h264-ETHEL')[1]['season'], 1)
        self.assertEqual(releaseInfo('Severance Season 2 Complete')[1]['season'], 2)
        episode = rankRelease('Severance.S02E03.720p.WEB', reference)
        for pack in ('Severance.S01.1080p.WEB.h264-ETHEL', 'Severance Season 1'):
            self.assertLessEqual(rankRelease(pack, reference), 10)
            self.assertGreater(episode, rankRelease(pack, reference))
        self.assertLess(rankRelease('Severance.S02.1080p.WEB.h264-ETHEL', reference), rankRelease('Severance.S02E03.1080p.WEB.h264-ETHEL', reference))

    def test_multi_episode(self):
        self.assertEqual(releaseInfo('The.Office.US.S05E10E11.720p')[1]['episode'], (5, 10))
        for reference in ('The.Office.US.S05E10.720p.HDTV.x264-CTU.mkv', 'The.Office.US.S05E11.720p.HDTV.x264-CTU.mkv'):
            self.assertGreater(rankRelease('The.Office.US.S05E10E11.720p', reference), 50)
        self.assertLessEqual(rankRelease('The.Office.US.S05E10E11.720p', 'The.Office.US.S05E12.720p.mkv'), 10)

    def test_sort_sync_first(self):
        seeker = SubsSeeker.__new__(SubsSeeker)
        subs = [{'filename': 'Movie.2019.720p.HDTV.x264-AAA', 'sync': True},
                {'filename': 'Movie.2019.1080p.BluRay.x264-SPARKS', 'sync': False},
                {'filename': 'Movie.2019.DVDRip.XviD-BBB', 'sync': False}]
        ranked = seeker.sortSubtitlesList(subs, sort_rank=True, reference='Movie.2019.1080p.BluRay.x264-SPARKS.mkv')
        self.assertEqual([s['filename'] for s in ranked], ['Movie.2019.720p.HDTV.x264-AAA', 'Movie.2019.1080p.BluRay.x264-SPARKS', 'Movie.2019.DVDRip.XviD-BBB'])
        self.assertTrue(ranked[1]['rank'] > ranked[2]['rank'])
        self.assertEqual(rankRelease('', 'x'), 0)


if __name__ == "__main__":
    unittest.main()
