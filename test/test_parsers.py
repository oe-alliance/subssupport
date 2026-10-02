import os
import sys
import unittest

test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..', 'plugin'))

from parsers import SubRipParser, MicroDVDParser
from parsers.baseparser import NoSubtitlesParseError


def cue(idx, start, end, text):
    return "%d\n00:00:%02d,000 --> 00:00:%02d,000\n%s\n\n" % (idx, start, end, text)


class TestSubRip(unittest.TestCase):
    def setUp(self):
        self.parser = SubRipParser()

    def test_one_cue(self):
        subs = self.parser.parse(cue(1, 1, 2, 'only one'))
        self.assertEqual([s['text'] for s in subs], ['only one'])

    def test_no_cue(self):
        self.assertRaises(NoSubtitlesParseError, self.parser.parse, 'no subtitles here')

    def test_empty_cue(self):
        subs = self.parser.parse(cue(1, 1, 2, '') + cue(2, 3, 4, 'second') + cue(3, 5, 6, 'third'))
        self.assertEqual([(s['start'] // 90, s['text']) for s in subs], [(3000, 'second'), (5000, 'third')])

    def test_number_line(self):
        subs = self.parser.parse(cue(1, 1, 2, 'The answer is\n42') + cue(2, 3, 4, '2001'))
        self.assertEqual([s['text'] for s in subs], ['The answer is\n42', '2001'])

    def test_missing_number_and_blank_line(self):
        text = "1\n00:00:01,000 --> 00:00:02,000\nfirst\n2\n00:00:03,000 --> 00:00:04,000\nsecond\n\n00:00:05,000 --> 00:00:06,000\nthird\n"
        self.assertEqual([s['text'] for s in self.parser.parse(text)], ['first', 'second', 'third'])

    def test_sorted(self):
        subs = self.parser.parse(cue(1, 5, 6, 'late') + cue(2, 1, 2, 'early'))
        self.assertEqual([s['text'] for s in subs], ['early', 'late'])

    def test_row_colors(self):
        self.parser.rowParse = True
        subs = self.parser.parse(cue(1, 1, 2, '<font color="#ff0000">red\nstill red</font>') + cue(2, 3, 4, "<font color=yellow>y</font>\nplain"))
        self.assertEqual([[(r['text'], r['color']) for r in s['rows']] for s in subs],
                         [[('red', 'ff0000'), ('still red', 'ff0000')], [('y', 'FFFF00'), ('plain', 'default')]])


class TestMicroDVD(unittest.TestCase):
    def test_fps_header(self):
        subs = MicroDVDParser().parse("{1}{1}23.976\n{25}{50}Hello|there\n{75}{100}Second\n", 25)
        self.assertEqual([(s['start'] // 90, s['text']) for s in subs], [(1000, 'Hello\nthere'), (3000, 'Second')])


if __name__ == "__main__":
    unittest.main()
