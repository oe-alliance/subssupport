import json
import os
import shutil
import sys
import tempfile
import unittest
test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..', 'plugin'))
from utils import SubsSyncStore


class TestSyncStore(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, 'sub', 'subssync.json')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_roundtrip(self):
        store = SubsSyncStore(self.path)
        self.assertIsNone(store.get('/hdd/a.mkv', '/hdd/a.srt'))
        self.assertTrue(store.set('/hdd/a.mkv', '/hdd/a.srt', -1200, 25.0, 'windows-1250', 1.042709))
        self.assertFalse(store.set('/hdd/a.mkv', '/hdd/a.srt', -1200, 25.0, 'windows-1250', 1.042709))  # unchanged
        self.assertTrue(store.save())
        store = SubsSyncStore(self.path)
        entry = store.get('/hdd/a.mkv', '/hdd/a.srt')
        self.assertEqual((entry['delay'], entry['fps'], entry['enc'], entry['ratio']), (-1200, 25.0, 'windows-1250', 1.042709))
        # other subtitle of the same video: no entry
        self.assertIsNone(store.get('/hdd/a.mkv', '/hdd/b.srt'))
        # subtitle loaded before the service started (unknown video): found by its path
        self.assertEqual(store.get(None, '/hdd/a.srt')['delay'], -1200)
        self.assertEqual(store.get('/hdd/a.mkv')['subs'], '/hdd/a.srt')

    def test_reset_removes(self):
        store = SubsSyncStore(self.path)
        store.set('v', 's', 400)
        self.assertTrue(store.set('v', 's', 0))
        self.assertIsNone(store.get('v', 's'))
        self.assertFalse(store.set('v', 's', 0))
        self.assertFalse(store.set(None, 's', 400))

    def test_limit(self):
        store = SubsSyncStore(self.path, limit=200)
        for i in range(250):
            store.set('video%d' % i, 'subs%d' % i, i + 1)
            store.data['video%d' % i]['time'] = i  # same second
        self.assertEqual(len(store.data), 200)
        self.assertIsNone(store.get('video49'))
        self.assertEqual(store.get('video249')['delay'], 250)
        store.save()
        self.assertLess(os.path.getsize(self.path), 200 * 120)

    def test_two_instances(self):
        # two players with their own store: no entry gets lost
        a, b = SubsSyncStore(self.path), SubsSyncStore(self.path)
        a.set('va', 'sa', 100)
        b.set('vb', 'sb', 200)
        b.set('vc', 'sc', 300)
        self.assertTrue(a.save())
        self.assertTrue(b.save())
        store = SubsSyncStore(self.path)
        self.assertEqual([store.get(v)['delay'] for v in ('va', 'vb', 'vc')], [100, 200, 300])
        # a removal is kept as well
        a.set('vc', 'sc', 0)  # a does not know vc
        b.set('vc', 'sc', 0)
        b.save()
        a.set('va', 'sa', 150)
        a.save()
        store = SubsSyncStore(self.path)
        self.assertEqual((store.get('va')['delay'], store.get('vb')['delay'], store.get('vc')), (150, 200, None))

    def test_relative_path(self):
        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            store = SubsSyncStore('subssync.json')
            store.set('v', 's', 100)
            self.assertTrue(store.save())
            self.assertEqual(SubsSyncStore('subssync.json').get('v')['delay'], 100)
        finally:
            os.chdir(cwd)

    def test_broken_file(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, 'w') as f:
            f.write('[1, 2')
        store = SubsSyncStore(self.path)
        self.assertIsNone(store.get('v', 's'))
        store.set('v', 's', 200)
        store.save()
        with open(self.path) as f:
            self.assertEqual(json.load(f)['v']['delay'], 200)


if __name__ == "__main__":
    unittest.main()
