import codecs
import json
import os
import re
import time

from urllib.request import Request, urlopen


def load(subpath):
    if subpath.startswith('http'):
        with urlopen(Request(subpath), timeout=30) as response:
            return response.read()
    with open(subpath, 'rb') as f:  # OSError -> LoadError in process.py
        return f.read()


def toUnicode(text):
    if isinstance(text, bytes):
        text = text.decode("UTF-8", errors='ignore')
    return text


def _codecName(enc):
    try:
        name = codecs.lookup(enc).name
    except LookupError:
        return enc.lower()
    # utf-16 = utf-16-le/be with or without BOM
    return re.sub(r'^(utf-(?:16|32))-[lb]e$', r'\1', name)


def detectEncoding(text, encodings):
    """Best guess of charset_normalizer/chardet when it is one of encodings, else None."""
    names = {_codecName(enc): enc for enc in reversed(encodings)}
    try:
        from charset_normalizer import from_bytes
        isolation = [n for n in names if n not in ('utf-8', 'utf-16', 'utf-32')]
        # threshold: dense diacritics (Polish iso-8859-2) look chaotic with the default 0.2
        best = from_bytes(text[:65536], cp_isolation=isolation or None, preemptive_behaviour=False, threshold=0.5).best()
        if best is not None and names.get(_codecName(best.encoding)):
            return names[_codecName(best.encoding)]
    except Exception as e:  # missing module or detector error
        if not isinstance(e, ImportError):
            print('[decode] charset_normalizer failed:', e)
    try:  # nothing found in the group
        import chardet
        result = chardet.detect(text[:65536])
        if result.get('encoding') and (result.get('confidence') or 0) >= 0.5:
            return names.get(_codecName(result['encoding']))
    except Exception:
        pass
    return None


def _utf16(text):
    """utf-16 codec for text with a BOM or the NUL bytes of ascii characters, else None"""
    if text.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return 'utf-16'
    sample = text[:4096]
    even, odd = sample[0::2].count(0), sample[1::2].count(0)
    if odd > len(sample) // 10 and even * 10 < odd:
        return 'utf-16-le'
    if even > len(sample) // 10 and odd * 10 < even:
        return 'utf-16-be'
    return None


def _decode(text, enc):
    # any even byte count "decodes" as utf-16, accept it only with a BOM or NUL pattern
    if _codecName(enc) == 'utf-16':
        codec = _utf16(text)
        if codec is None:
            raise ValueError('not utf-16')
        return text.decode(codec)
    return text.decode(enc)


def decode(text, encodings, current_encoding=None, decode_from_start=False, detect=True, preferred=None):
    utext = None
    used_encoding = None
    current_encoding_idx = -1
    current_idx = 0

    if decode_from_start or current_encoding not in encodings:  # encoding group changed
        current_encoding = None

    # encoding the user chose for this file before
    if current_encoding is None and preferred in encodings:
        try:
            return _decode(text, preferred), preferred
        except Exception:
            pass

    # first try: valid utf-8, then the detector guess limited to the encoding group
    if current_encoding is None and detect and len(encodings) > 1:
        guess = None
        if _utf16(text):
            guess = next((enc for enc in encodings if _codecName(enc) == 'utf-16'), None)
        elif _codecName(encodings[0]) == 'utf-8':
            try:
                return text.decode(encodings[0]), encodings[0]
            except UnicodeDecodeError:
                pass
        guess = guess or detectEncoding(text, encodings)
        if guess:
            try:
                utext = _decode(text, guess)
                print('[decode] detected', guess, 'encoding')
                return utext, guess
            except Exception:
                pass

    if current_encoding is not None:
        current_encoding_idx = encodings.index(current_encoding)
        current_idx = current_encoding_idx + 1
        if current_idx >= len(encodings):
            current_idx = 0

    while current_idx != current_encoding_idx:
        enc = encodings[current_idx]
        try:
            print('[decode] trying encoding', enc, '...')
            utext = _decode(text, enc)
            print('[decode] decoded with', enc, 'encoding')
            used_encoding = enc
            return utext, used_encoding
        except Exception:
            if enc == encodings[-1] and current_encoding_idx == -1:
                print('[decode] cannot decode with provided encodings')
                raise Exception("decode error")
            elif enc == encodings[-1] and current_encoding_idx != -1:
                current_idx = 0
                continue
            else:
                current_idx += 1
                continue


class SubsSyncStore(object):
    """Delay/fps/encoding per video, {video: {'subs':, 'delay':, 'fps':, 'enc':, 'time':}}, newest entries kept"""

    def __init__(self, path, limit=200):
        self.path = path
        self.limit = limit
        self.data = None
        self.changes = {}  # {video: entry or None (removed)} since the last save

    def _load(self):
        if self.data is None:
            try:
                with open(self.path, 'r') as f:
                    self.data = json.load(f)
                if not isinstance(self.data, dict):
                    raise ValueError("not a dict")
            except Exception as e:
                if os.path.exists(self.path):
                    print('[SubsSyncStore] cannot load %s: %s' % (self.path, e))
                self.data = {}
        return self.data

    def get(self, video, subsPath=None):
        """entry of video, or the newest one of subsPath (players which load subtitles before the service starts)"""
        data = self._load()
        entry = video and data.get(video)
        if entry and (subsPath is None or entry.get('subs') == subsPath):
            return entry
        entries = [e for e in data.values() if subsPath and e.get('subs') == subsPath]
        return entries and max(entries, key=lambda e: e.get('time', 0)) or None

    def set(self, video, subsPath, delay=0, fps=None, enc=None, ratio=None):
        """returns True when the store changed, default values remove the entry
        ratio = subtitles fps / video fps, fps is informational"""
        data = self._load()
        if not video:
            return False
        if not delay and not ratio and enc is None:
            if data.pop(video, None) is None:
                return False
            self.changes[video] = None
            return True
        entry = {'subs': subsPath, 'delay': int(delay), 'fps': fps, 'ratio': ratio, 'enc': enc, 'time': int(time.time())}
        old = data.get(video)
        if old and dict(old, time=0) == dict(entry, time=0):
            return False
        data[video] = self.changes[video] = entry
        self._limit(data)
        return True

    def _limit(self, data):
        if len(data) > self.limit:
            for key in sorted(data, key=lambda k: data[k].get('time', 0))[:len(data) - self.limit]:
                del data[key]

    def save(self):
        if self.data is None:
            return False
        try:
            # merge into the current file, other players may have saved meanwhile
            self.data = None
            data = self._load()
            for video, entry in self.changes.items():
                if entry is None:
                    data.pop(video, None)
                else:
                    data[video] = entry
            self._limit(data)
            folder = os.path.dirname(self.path)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder)
            tmp = self.path + '.tmp'
            with open(tmp, 'w') as f:
                json.dump(data, f, separators=(',', ':'))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
            self.changes = {}
            return True
        except Exception as e:
            print('[SubsSyncStore] cannot save %s: %s' % (self.path, e))
            return False


class HeadRequest(Request):
    def get_method(self):
        return "HEAD"


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


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
