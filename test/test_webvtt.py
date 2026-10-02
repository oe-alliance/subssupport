import os
import shutil
import sys
import tempfile
import types
import unittest

test = os.path.dirname(os.path.realpath(__file__))
plugin = types.ModuleType('SubsSupport')
plugin.__path__ = [os.path.join(test, '..', 'plugin')]
sys.modules['SubsSupport'] = plugin

from SubsSupport.parsers import SubRipParser, SubViewerParser, MicroDVDParser, AssParser, WebVTTParser
from SubsSupport.process import SubsLoader

VTT = u"""\ufeffWEBVTT - some title
Kind: captions
Language: en

NOTE this is a comment
spanning two lines

STYLE
::cue(.yellow) { color: yellow }

REGION
id:fred width:40%

1
00:00:01.000 --> 00:00:02.500 align:start position:10% line:0
<v Roger Bingham>We are in New York City</v>

intro-2
00:03.200 --> 00:04.000
<i>Second</i> &amp; <b>bold</b>
second &lt;line&gt;

01:02:03.5 --> 01:02:04.250 size:50%
<c.yellow.bg_black>Third</c> cue<00:00:03.500>karaoke

NOTE a final note

00:00:05.000 --> 00:00:06.000
\u202b\u0645\u0631\u062d\u0628\u0627\u202c
"""


class TestWebVTT(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def load(self, name, text, row=False):
        path = os.path.join(self.tmp, name)
        with open(path, 'wb') as f:
            f.write(text.replace('\n', '\r\n').encode('utf-8'))
        loader = SubsLoader([SubRipParser, SubViewerParser, MicroDVDParser, AssParser, WebVTTParser], ['utf-8'])
        loader.set_row_parsing(row)
        return loader.load(path, fps=25)[0]

    def test_cues(self):
        subs = self.load('a.vtt', VTT)
        # sorted by start time
        self.assertEqual([s['start'] // 90 for s in subs], [1000, 3200, 5000, 3723500])
        self.assertEqual([s['end'] // 90 for s in subs], [2500, 4000, 6000, 3724250])
        self.assertEqual(subs[0]['text'], u'We are in New York City')
        self.assertEqual(subs[1]['text'], u'Second & bold\nsecond <line>')
        self.assertEqual(subs[1]['style'], 'italic')
        self.assertEqual(subs[3]['text'], u'Third cuekaraoke')
        self.assertEqual(subs[3]['color'], 'FFFF00')
        self.assertEqual(subs[2]['text'], u'\u0645\u0631\u062d\u0628\u0627')
        self.assertEqual(subs[0]['duration'], 1500)

    def test_row_parsing(self):
        subs = self.load('b.vtt', VTT, row=True)
        self.assertEqual([r['text'] for r in subs[1]['rows']], [u'Second & bold', u'second <line>'])

    def test_wrong_extension(self):
        # .srt with WebVTT content falls back to the WebVTT parser
        self.assertEqual(len(self.load('c.srt', VTT)), 4)

    def test_extension(self):
        self.assertTrue(WebVTTParser.canParse('.VTT'))
        self.assertFalse(SubRipParser.canParse('.vtt'))


if __name__ == "__main__":
    unittest.main()
