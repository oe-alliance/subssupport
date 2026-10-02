from html import unescape
import re

from .baseparser import ParseError, HEX_COLORS
from .subrip import SubRipParser

TIMING_RE = re.compile(r'^\s*((?:\d+:)?\d{1,2}:\d{2}[.,]\d{1,3})\s*-->\s*((?:\d+:)?\d{1,2}:\d{2}[.,]\d{1,3})(?:\s.*)?$')
COLOR_RE = re.compile(r'<c(?:\.[\w-]+)*\.([a-z]+)(?:\.[\w-]+)*>', re.I)


def vttTime(value):
    """hh:mm:ss.mmm or mm:ss.mmm -> ms"""
    parts = value.replace(',', '.').split(':')
    secs, ms = parts[-1].split('.')
    hours = int(parts[0]) if len(parts) == 3 else 0
    return ((hours * 60 + int(parts[-2])) * 60 + int(secs)) * 1000 + int(ms.ljust(3, '0'))


class WebVTTParser(SubRipParser):
    """WebVTT (.vtt): header, NOTE/STYLE/REGION blocks are skipped, cue settings ignored."""
    format = "WebVTT"
    parsing = ('.vtt',)

    def _parse(self, text, fps):
        subs = []
        for idx, block in enumerate(re.split(r'\n[ \t]*\n', text)):
            lines = block.strip('\n').split('\n')
            first = lines[0].strip()
            if not first or (idx == 0 and first.startswith('WEBVTT')) or re.match(r'(NOTE|STYLE|REGION)(\s|$)', first):
                continue
            if '-->' not in first:  # cue identifier
                lines = lines[1:]
            if not lines:
                continue
            timing = TIMING_RE.match(lines[0])
            if timing is None:
                continue
            try:
                start, end = vttTime(timing.group(1)), vttTime(timing.group(2))
            except ValueError as e:
                raise ParseError('%s, cue: %d' % (str(e), len(subs) + 1)) from e
            sub_text = '\n'.join(lines[1:]).strip()
            if sub_text:
                subs.append(self.createSub(sub_text, start, end))
        return subs

    def _removeTags(self, text):
        # <v Name>, <c.class>, <i>, <b>, <u>, <ruby>, <00:00:01.000> are dropped by the SubRip cleanup
        return unescape(SubRipParser._removeTags(self, text)).replace('\u00a0', ' ')

    def _getColor(self, text, color):
        match = COLOR_RE.search(text)
        if match and match.group(1).lower() in HEX_COLORS:
            return HEX_COLORS[match.group(1).lower()][1:], 'default'
        return 'default', 'default'


parserClass = WebVTTParser
