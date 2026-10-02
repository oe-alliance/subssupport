import os
import sys
import types
import unittest
from unittest import mock
test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..', 'plugin'))
from utils import decode

SUBS_PATH = os.path.join(test, 'subfiles')
UTF = ['utf-8', 'utf-16']
CENTRAL_EUROPE = UTF + ['windows-1250', 'iso-8859-2', 'maclatin2', 'IBM852']
ARABIC = UTF + ['windows-1256', 'iso-8859-6', 'IBM864']
MIXED = UTF + ['windows-1252', 'windows-1250', 'iso-8859-2', 'windows-1256', 'windows-1251', 'koi8_r']
POLISH = u'1\n00:00:01,000 --> 00:00:02,000\nZażółć gęślą jaźń. Pchnąć w tę łódź jeża lub ośm skrzyń fig.\n\n'

try:
    import charset_normalizer  # noqa: F401
    DETECTOR = True
except ImportError:
    try:
        import chardet  # noqa: F401
        DETECTOR = True
    except ImportError:
        DETECTOR = False


def read(name):
    with open(os.path.join(SUBS_PATH, name), 'rb') as f:
        return f.read()


class TestDecode(unittest.TestCase):

    def test_cp1250(self):
        text, enc = decode(read('test_cp1250.srt'), CENTRAL_EUROPE)
        self.assertEqual(enc, 'windows-1250')
        self.assertIn(u'P\u0159\u00edli\u0161 \u017elu\u0165ou\u010dk\u00fd', text)

    def test_arabic_cp1256(self):
        text, enc = decode(read('test_arabic.srt'), ARABIC)
        self.assertEqual(enc, 'windows-1256')
        self.assertIn(u'\u062a\u0639\u062f\u064a\u0644', text)

    @unittest.skipUnless(DETECTOR, 'no charset detector installed')
    def test_detect_in_mixed_group(self):
        # first-decodable picks windows-1252 for both files
        text, enc = decode(read('test_arabic.srt'), MIXED)
        self.assertEqual(enc, 'windows-1256')
        self.assertIn(u'\u062a\u0639\u062f\u064a\u0644', text)
        text, enc = decode(read('test_cp1250.srt'), MIXED)
        self.assertEqual(enc, 'windows-1250')
        self.assertIn(u'\u017elu\u0165ou\u010dk\u00fd', text)

    @unittest.skipUnless(DETECTOR, 'no charset detector installed')
    def test_iso8859_2(self):
        text, enc = decode(read('test_iso8859_2.srt'), CENTRAL_EUROPE)
        self.assertEqual(enc, 'iso-8859-2')
        self.assertIn(u'Za\u017c\u00f3\u0142\u0107 g\u0119\u015bl\u0105', text)

    def test_restricted_to_group(self):
        # Arabic file, Central European group: never an encoding outside of the group
        enc = decode(read('test_arabic.srt'), CENTRAL_EUROPE)[1]
        self.assertIn(enc, CENTRAL_EUROPE)
        self.assertRaisesRegex(Exception, 'decode error', decode, read('test_arabic.srt'), ['utf-8'])

    def test_utf(self):
        self.assertEqual(decode(read('test_utf16.srt'), CENTRAL_EUROPE)[1], 'utf-16')
        self.assertEqual(decode(read('test_tags.srt'), CENTRAL_EUROPE)[1], 'utf-8')

    def test_next_encoding(self):
        # "change encoding" continues after the current one, no detection
        data = read('test_cp1250.srt')
        self.assertEqual(decode(data, CENTRAL_EUROPE, 'windows-1250')[1], 'iso-8859-2')
        self.assertEqual(decode(data, CENTRAL_EUROPE, 'IBM852')[1], 'windows-1250')
        self.assertEqual(decode(read('test_arabic.srt'), MIXED, detect=False)[1], 'windows-1252')
        # encoding group changed meanwhile
        self.assertEqual(decode(data, CENTRAL_EUROPE, 'windows-1256')[1], 'windows-1250')

    def test_utf16_without_bom(self):
        text = POLISH * 3
        for codec in ('utf-16-le', 'utf-16-be'):
            self.assertEqual(decode(text.encode(codec), CENTRAL_EUROPE), (text, 'utf-16'))
            self.assertEqual(decode(text.encode(codec), CENTRAL_EUROPE, preferred='utf-16'), (text, 'utf-16'))

    def test_no_utf16_guess(self):
        # 8-bit text with an even byte count is not utf-16 without BOM/NUL bytes
        data = (POLISH * 40).encode('iso-8859-2')
        self.assertNotEqual(decode(data, CENTRAL_EUROPE, detect=False)[1], 'utf-16')
        self.assertNotEqual(decode(data, CENTRAL_EUROPE, 'utf-8')[1], 'utf-16')

    @unittest.skipUnless(DETECTOR, 'no charset detector installed')
    def test_dense_iso8859_2(self):
        text = POLISH * 40
        self.assertEqual(decode(text.encode('iso-8859-2'), CENTRAL_EUROPE), (text, 'iso-8859-2'))

    def test_chardet_fallback(self):
        # charset_normalizer finds nothing -> chardet
        class Matches(object):
            def best(self):
                return None
        normalizer = types.ModuleType('charset_normalizer')
        normalizer.from_bytes = lambda *args, **kwargs: Matches()
        chardet = types.ModuleType('chardet')
        chardet.detect = lambda data: {'encoding': 'ISO-8859-2', 'confidence': 0.8}
        with mock.patch.dict(sys.modules, {'charset_normalizer': normalizer, 'chardet': chardet}):
            self.assertEqual(decode((POLISH * 40).encode('iso-8859-2'), CENTRAL_EUROPE)[1], 'iso-8859-2')


if __name__ == "__main__":
    unittest.main()
